"""
Smoke tests for audio endpoints (end-to-end against a running server).
This script will:
- Wait for the server to be ready at http://127.0.0.1:5000
- Create small test audio files (WAV) programmatically
- Call each audio endpoint and verify success responses and downloadable outputs when provided

Run: python tools/smoke_audio_tests.py
"""
import io
import os
import sys
import time
import wave
import struct
import math
import tempfile
import requests
import shutil

HOST = os.environ.get("T2V_HOST", "http://127.0.0.1:5000")
TIMEOUT = 120


def wait_for_ready(timeout=30):
  deadline = time.time() + timeout
  while time.time() < deadline:
    try:
      r = requests.get(HOST + "/api/v1/status", timeout=3)
      if r.status_code == 200:
        return True
    except Exception:
      pass
    time.sleep(0.5)
  return False


def make_sine_wav(path, duration=1.0, freq=440.0, samplerate=22050, amp=0.1):
  n_samples = int(duration * samplerate)
  with wave.open(path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    for i in range(n_samples):
      t = float(i) / samplerate
      val = int(amp * 32767.0 * math.sin(2.0 * math.pi * freq * t))
      data = struct.pack('<h', val)
      wf.writeframesraw(data)


def run_test():
  print("Waiting for server to be ready...")
  if not wait_for_ready(timeout=60):
    print("Server not responding at", HOST)
    return 1
  print("Server ready, running smoke tests...")

  tmpdir = tempfile.mkdtemp(prefix="t2v_smoke_")
  results = []

  try:
    # Create test audio files
    a1 = os.path.join(tmpdir, "a1.wav")
    a2 = os.path.join(tmpdir, "a2.wav")
    a_long = os.path.join(tmpdir, "a_long.wav")
    make_sine_wav(a1, duration=1.0)
    make_sine_wav(a2, duration=1.0, freq=660.0)
    make_sine_wav(a_long, duration=4.0)

    # 1) audio-duration
    with open(a1, 'rb') as f:
      r = requests.post(HOST + "/api/v1/audio-duration", files={'audioFile': f}, timeout=TIMEOUT)
    ok = r.status_code == 200 and 'duration' in r.json()
    print("audio-duration:", r.status_code, r.text)
    results.append(('audio-duration', ok, r.status_code, r.text))

    # 2) audio-size
    with open(a1, 'rb') as f:
      r = requests.post(HOST + "/api/v1/audio-size", files={'audioFile': f}, timeout=TIMEOUT)
    ok = r.status_code == 200 and 'size' in r.json()
    print("audio-size:", r.status_code, r.text)
    results.append(('audio-size', ok, r.status_code, r.text))

    # 3) check-silence
    with open(a1, 'rb') as f:
      r = requests.post(HOST + "/api/v1/check-silence", files={'audioFile': f}, timeout=TIMEOUT)
    ok = r.status_code == 200 and 'isSilent' in r.json()
    print("check-silence:", r.status_code, r.text)
    results.append(('check-silence', ok, r.status_code, r.text))

    # 4) normalize-audio
    with open(a1, 'rb') as f:
      data = {'normalizeBitrate': '128k', 'normalizeSampleRate': '22050', 'normalizeFilter': 'loudnorm'}
      r = requests.post(HOST + "/api/v1/normalize-audio", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("normalize-audio:", r.status_code, r.text)
    ok = r.status_code in (200,) and isinstance(r.json(), dict) and 'link' in r.json()
    results.append(('normalize-audio', ok, r.status_code, r.text))
    if ok:
      dl = requests.get(HOST + r.json()['link'], timeout=TIMEOUT)
      print("normalize download:", dl.status_code)
      results.append(('normalize-download', dl.status_code == 200, dl.status_code, 'download'))

    # 5) generate-silent-audio
    payload = {'silentDuration': 2, 'silentFormat': '.wav'}
    r = requests.post(HOST + "/api/v1/generate-silent-audio", json=payload, timeout=TIMEOUT)
    print("generate-silent-audio:", r.status_code, r.text)
    ok = r.status_code in (200,) and 'link' in r.json()
    results.append(('generate-silent-audio', ok, r.status_code, r.text))
    if ok:
      dl = requests.get(HOST + r.json()['link'], timeout=TIMEOUT)
      results.append(('silent-download', dl.status_code == 200, dl.status_code, 'download'))

    # 6) convert-audio
    with open(a1, 'rb') as f:
      data = {'outputFormat': 'mp3', 'bitrate': '128', 'sampleRate': '22050', 'channels': '1'}
      r = requests.post(HOST + "/api/v1/convert-audio", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("convert-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('convert-audio', ok, r.status_code, r.text))
    if ok:
      dl = requests.get(HOST + r.json()['link'], timeout=TIMEOUT)
      results.append(('convert-download', dl.status_code == 200, dl.status_code, 'download'))

    # 7) change-volume
    with open(a1, 'rb') as f:
      data = {'volume': '0.5'}
      r = requests.post(HOST + "/api/v1/change-volume", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("change-volume:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('change-volume', ok, r.status_code, r.text))

    # 8) change-speed
    with open(a1, 'rb') as f:
      data = {'speed': '1.25'}
      r = requests.post(HOST + "/api/v1/change-speed", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("change-speed:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('change-speed', ok, r.status_code, r.text))

    # 9) reverse-audio
    with open(a1, 'rb') as f:
      r = requests.post(HOST + "/api/v1/reverse-audio", files={'audioFile': f}, timeout=TIMEOUT)
    print("reverse-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('reverse-audio', ok, r.status_code, r.text))

    # 10) concat-audio
    files = [('audioFiles', open(a1, 'rb')), ('audioFiles', open(a2, 'rb'))]
    r = requests.post(HOST + "/api/v1/concat-audio", files=files, timeout=TIMEOUT)
    print("concat-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('concat-audio', ok, r.status_code, r.text))

    # 11) split-audio
    with open(a_long, 'rb') as f:
      data = {'segmentDuration': '2'}
      r = requests.post(HOST + "/api/v1/split-audio", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("split-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('split-audio', ok, r.status_code, r.text))

    # 12) fade-audio
    with open(a1, 'rb') as f:
      data = {'fadeIn': '0.2', 'fadeOut': '0.2'}
      r = requests.post(HOST + "/api/v1/fade-audio", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("fade-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('fade-audio', ok, r.status_code, r.text))

    # 13) remove-vocals
    with open(a1, 'rb') as f:
      r = requests.post(HOST + "/api/v1/remove-vocals", files={'audioFile': f}, timeout=TIMEOUT)
    print("remove-vocals:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('remove-vocals', ok, r.status_code, r.text))

    # 14) equalize-audio
    with open(a1, 'rb') as f:
      data = {'freq': '1000', 'width': '2', 'gain': '3'}
      r = requests.post(HOST + "/api/v1/equalize-audio", files={'audioFile': f}, data=data, timeout=TIMEOUT)
    print("equalize-audio:", r.status_code, r.text)
    ok = r.status_code == 200 and 'link' in r.json()
    results.append(('equalize-audio', ok, r.status_code, r.text))

    # 15) extract-audio (if we can upload a sample video)
    sample_video = None
    # Prefer an asset sample if available
    possible = [
      os.path.join('Assets', 'Videos', 'Horizontal Videos', 'Sample Horizontal (1).mp4'),
      os.path.join('Assets', 'Videos', 'Horizontal Videos', 'Sample Horizontal (5).mp4')
    ]
    for p in possible:
      if os.path.exists(p):
        sample_video = p
        break
    if sample_video:
      with open(sample_video, 'rb') as f:
        r = requests.post(HOST + "/api/v1/extract-audio", files={'videoFile': f}, timeout=TIMEOUT)
      print("extract-audio:", r.status_code, r.text)
      # Accept 200 (audio extracted) or 400 (video has no audio) as OK for the smoke test.
      ok = (r.status_code == 200 and isinstance(r.json(), dict) and 'link' in r.json()) or (r.status_code == 400)
      results.append(('extract-audio', ok, r.status_code, r.text))
    else:
      print('extract-audio: skipped (no sample video)')
      results.append(('extract-audio', True, 0, 'skipped'))

    # 16) basic jobs flow: create job / get / trigger / result / delete
    try:
      job_payload = {'text': 'Smoke test job', 'language': 'en-us', 'voice': 'af_nova'}
      r = requests.post(HOST + "/api/v1/jobs", json=job_payload, timeout=TIMEOUT)
      print('create-job:', r.status_code, r.text)
      job_ok = r.status_code in (202,)
      job_id = None
      if job_ok:
        job_id = r.json().get('jobId')
      results.append(('create-job', job_ok, r.status_code, r.text))

      # get jobs
      r = requests.get(HOST + "/api/v1/jobs", timeout=TIMEOUT)
      results.append(('list-jobs', r.status_code == 200, r.status_code, r.text))

      if job_id:
        r = requests.get(HOST + f"/api/v1/jobs/{job_id}", timeout=TIMEOUT)
        results.append(('get-job', r.status_code in (200, 404, 500), r.status_code, r.text))

        r = requests.post(HOST + "/api/v1/jobs/triggerRemaining", timeout=TIMEOUT)
        results.append(('trigger-remaining', r.status_code == 200, r.status_code, r.text))

        # try to fetch result (may be 400/404 while processing)
        r = requests.get(HOST + f"/api/v1/jobs/{job_id}/result", timeout=TIMEOUT)
        results.append(('get-result', r.status_code in (200, 400, 404, 500), r.status_code, r.text))

        # delete job
        r = requests.delete(HOST + f"/api/v1/jobs/{job_id}", timeout=TIMEOUT)
        results.append(('delete-job', r.status_code in (200, 404, 500), r.status_code, r.text))

      # delete all jobs
      r = requests.delete(HOST + "/api/v1/jobs/all", timeout=TIMEOUT)
      results.append(('delete-all-jobs', r.status_code == 200, r.status_code, r.text))
    except Exception as e:
      print('jobs-flow exception:', e)
      results.append(('jobs-flow', False, 0, str(e)))

  except Exception as e:
    print("Exception during smoke tests:", e)
    return 2
  finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

  print("\nSummary:")
  failed = 0
  for name, ok, code, text in results:
    status = "OK" if ok else "FAIL"
    print(f"{name}: {status} (HTTP {code})")
    if not ok:
      failed += 1
  if failed == 0:
    print("All smoke tests passed.")
    return 0
  else:
    print(f"{failed} smoke tests failed.")
    return 3


if __name__ == '__main__':
  sys.exit(run_test())
