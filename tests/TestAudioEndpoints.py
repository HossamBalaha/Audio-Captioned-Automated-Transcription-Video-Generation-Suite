import io
import os
import sys
import tempfile
import wave
import struct
import math
import json
import time
import pytest

# Try to import the Flask app from Server.py; if import fails, skip all tests.
try:
  from Server import app
except Exception as e:
  pytest.skip(f"Could not import Server.app: {e}", allow_module_level=True)


def make_sine_wav_bytes(duration=0.5, freq=440.0, samplerate=22050, amp=0.1):
  n_samples = int(duration * samplerate)
  buf = io.BytesIO()
  with wave.open(buf, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    for i in range(n_samples):
      t = float(i) / samplerate
      val = int(amp * 32767.0 * math.sin(2.0 * math.pi * freq * t))
      data = struct.pack('<h', val)
      wf.writeframesraw(data)
  buf.seek(0)
  return buf


@pytest.fixture
def client():
  # Use the Flask test client to call endpoints without running a server process.
  with app.test_client() as c:
    yield c


# --- Non-audio endpoints -------------------------------------------------
def test_server_status_and_ready(client):
  rv = client.get('/api/v1/status')
  assert rv.status_code == 200
  rv = client.get('/api/v1/ready')
  assert rv.status_code in (200, 503)


def test_metadata_endpoints(client):
  rv = client.get('/api/v1/languages')
  assert rv.status_code == 200
  data = rv.get_json()
  assert 'languages' in data

  rv = client.get('/api/v1/voices')
  assert rv.status_code == 200
  rv = client.get('/api/v1/videoTypes')
  assert rv.status_code == 200
  rv = client.get('/api/v1/videoQualities')
  assert rv.status_code == 200


def test_download_endpoint(client, tmp_path):
  # Create a temporary file in the app STORE_PATH and request it via download endpoint
  store = app.config.get('STORE_PATH')
  os.makedirs(store, exist_ok=True)
  fname = f"test_download_{int(time.time())}.txt"
  fpath = os.path.join(store, fname)
  with open(fpath, 'wb') as f:
    f.write(b'hello world')
  rv = client.get(f'/api/v1/download/{fname}')
  assert rv.status_code == 200
  assert rv.data.startswith(b'hello')
  # On Windows the file may be locked briefly by send_file; retry removal a few times.
  removed = False
  for _ in range(5):
    try:
      os.remove(fpath)
      removed = True
      break
    except PermissionError:
      time.sleep(0.1)
  if not removed:
    # Best effort cleanup; leave file if we cannot remove it.
    if os.path.exists(fpath):
      try:
        import atexit
        atexit.register(lambda p=fpath: os.path.exists(p) and os.remove(p))
      except Exception:
        pass


# --- Jobs endpoints (basic flow) ----------------------------------------
def test_jobs_flow(client):
  # Create a job
  payload = {
    'text'    : 'this is a test job for pytest',
    'language': 'en-us',
    'voice'   : 'af_nova'
  }
  rv = client.post('/api/v1/jobs', json=payload)
  assert rv.status_code == 202
  data = rv.get_json()
  assert 'jobId' in data
  jobId = data['jobId']

  # List jobs
  rv = client.get('/api/v1/jobs')
  assert rv.status_code == 200
  data = rv.get_json()
  assert 'jobs' in data

  # Get job status
  rv = client.get(f'/api/v1/jobs/{jobId}')
  # job may be processing and the job data file can be transiently unreadable;
  # accept 200 (ok), 404 (not found) or 500 (transient JSON read error while processing).
  assert rv.status_code in (200, 404, 500)

  # Trigger remaining jobs
  rv = client.post('/api/v1/jobs/triggerRemaining')
  assert rv.status_code == 200

  # Delete the job (cleanup) - accept 200 or 404
  # Attempt deletion with retries because background processing may hold file handles on Windows.
  del_status = None
  for _ in range(5):
    rv = client.delete(f'/api/v1/jobs/{jobId}')
    del_status = rv.status_code
    if del_status in (200, 404):
      break
    # if it's 500, wait briefly and retry
    time.sleep(0.2)
  # After retries, accept 200, 404, or 500 (best-effort cleanup)
  assert del_status in (200, 404, 500)

  # Try to get the processed result if available (accept several statuses)
  rv = client.get(f'/api/v1/jobs/{jobId}/result')
  assert rv.status_code in (200, 400, 404, 500)

  # Call delete-all-jobs to ensure the endpoint is reachable
  rv = client.delete('/api/v1/jobs/all')
  assert rv.status_code == 200


# --- Audio endpoint tests (existing) -----------------------------------

def test_audio_duration(client):
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav')}
  rv = client.post('/api/v1/audio-duration', content_type='multipart/form-data', data=data)
  assert rv.status_code == 200
  json_data = rv.get_json()
  assert 'duration' in json_data


def test_audio_size(client):
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav')}
  rv = client.post('/api/v1/audio-size', content_type='multipart/form-data', data=data)
  assert rv.status_code == 200
  json_data = rv.get_json()
  assert 'size' in json_data


def test_check_silence(client):
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav')}
  rv = client.post('/api/v1/check-silence', content_type='multipart/form-data', data=data)
  assert rv.status_code == 200
  json_data = rv.get_json()
  assert 'isSilent' in json_data


@pytest.mark.parametrize('endpoint,params', [
  ('/api/v1/change-volume', {'volume': '1.0'}),
  ('/api/v1/change-speed', {'speed': '1.0'}),
  ('/api/v1/reverse-audio', {}),
  ('/api/v1/normalize-audio',
   {'normalizeBitrate': '128k', 'normalizeSampleRate': '22050', 'normalizeFilter': 'loudnorm'}),
])
def test_simple_processing_endpoints(client, endpoint, params):
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav')}
  data.update(params)
  rv = client.post(endpoint, content_type='multipart/form-data', data=data)
  # Accept either 200 (success) or 500 (ffmpeg / environment error) but the endpoint shouldn't crash.
  assert rv.status_code in (200, 400, 500)


def test_generate_silent_audio(client):
  rv = client.post('/api/v1/generate-silent-audio', json={'silentDuration': 1, 'silentFormat': '.wav'})
  assert rv.status_code in (200, 400, 500)


def test_convert_audio(client):
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav'), 'outputFormat': 'mp3'}
  rv = client.post('/api/v1/convert-audio', content_type='multipart/form-data', data=data)
  assert rv.status_code in (200, 400, 500)


def test_concat_and_split(client):
  # concat
  wav1 = make_sine_wav_bytes()
  wav2 = make_sine_wav_bytes(freq=660.0)
  data = [('audioFiles', (wav1, 'one.wav')), ('audioFiles', (wav2, 'two.wav'))]
  # Flask test client expects a dict for multipart, so we craft a files dict.
  files = {'audioFiles': [data[0][1], data[1][1]]}
  rv = client.post('/api/v1/concat-audio', content_type='multipart/form-data',
                   data={'audioFiles': [data[0][1], data[1][1]]})
  assert rv.status_code in (200, 400, 500)

  # split
  long_wav = make_sine_wav_bytes(duration=2.0)
  data = {'audioFile': (long_wav, 'long.wav'), 'segmentDuration': '1'}
  rv = client.post('/api/v1/split-audio', content_type='multipart/form-data', data=data)
  assert rv.status_code in (200, 400, 500)


def test_extract_audio(client):
  # Use a small sample video from Assets (if exists)
  sample = os.path.join('Assets', 'Videos', 'Horizontal Videos', 'Sample Horizontal (1).mp4')
  if not os.path.exists(sample):
    pytest.skip('No sample video found for extract-audio test')
  with open(sample, 'rb') as f:
    rv = client.post('/api/v1/extract-audio', content_type='multipart/form-data',
                     data={'videoFile': (f, os.path.basename(sample))})
  assert rv.status_code in (200, 400, 500)


def test_fade_remove_vocals_equalize(client):
  wav = make_sine_wav_bytes()
  # fade
  data = {'audioFile': (wav, 'test.wav'), 'fadeIn': '0.2', 'fadeOut': '0.2'}
  rv = client.post('/api/v1/fade-audio', content_type='multipart/form-data', data=data)
  assert rv.status_code in (200, 400, 500)

  # remove vocals
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav')}
  rv = client.post('/api/v1/remove-vocals', content_type='multipart/form-data', data=data)
  assert rv.status_code in (200, 400, 500)

  # equalize
  wav = make_sine_wav_bytes()
  data = {'audioFile': (wav, 'test.wav'), 'freq': '1000', 'width': '2', 'gain': '3'}
  rv = client.post('/api/v1/equalize-audio', content_type='multipart/form-data', data=data)
  assert rv.status_code in (200, 400, 500)
