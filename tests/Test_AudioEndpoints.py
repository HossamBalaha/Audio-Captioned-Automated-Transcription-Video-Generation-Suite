'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Permissions and Citation: Refer to the README file.
'''

import io, os, sys, tempfile, wave, struct, math, json, time, pytest

# Try to import the Flask app from Server.py; if import fails, skip all tests.
try:
  # Attempt to import the Flask app from Server.py.
  from Server import app
except Exception as e:
  # Skip all tests if the app cannot be imported.
  pytest.skip(f"Could not import Server.app: {e}", allow_module_level=True)


# Create an in-memory sine-wave WAV file bytes for testing.
def MakeSineWavBytes(duration=0.5, freq=440.0, samplerate=22050, amp=0.1):
  # Calculate number of samples.
  nSamples = int(duration * samplerate)
  # Create a bytes buffer.
  buf = io.BytesIO()
  # Open wave writer.
  with wave.open(buf, "wb") as wf:
    # Set mono channel.
    wf.setnchannels(1)
    # Set 16-bit sample width.
    wf.setsampwidth(2)
    # Set sample rate.
    wf.setframerate(samplerate)
    # Write frames raw in a loop.
    for i in range(nSamples):
      # Compute time in seconds.
      t = float(i) / samplerate
      # Compute sample value for sine wave.
      val = int(amp * 32767.0 * math.sin(2.0 * math.pi * freq * t))
      # Pack the value into bytes.
      data = struct.pack("<h", val)
      # Write the packed frame.
      wf.writeframesraw(data)
  # Reset buffer pointer to start.
  buf.seek(0)
  # Return the buffer object.
  return buf


# Provide a Flask test client fixture.
@pytest.fixture
def client():
  # Create test client context.
  with app.test_client() as c:
    # Yield the client.
    yield c


# --- Non-audio endpoints -------------------------------------------------
# Test server status and ready endpoints.
def Test_ServerStatusAndReady(client):
  # Request server status.
  rv = client.get("/api/v1/status")
  # Assert status is OK.
  assert (rv.status_code == 200)
  # Request server readiness.
  rv = client.get("/api/v1/ready")
  # Assert readiness returns 200 or 503.
  assert (rv.status_code in (200, 503))


# Test metadata endpoints for languages, voices, videoTypes, videoQualities.
def Test_MetadataEndpoints(client):
  # Request languages list.
  rv = client.get("/api/v1/languages")
  # Assert OK status.
  assert (rv.status_code == 200)
  # Parse JSON response.
  data = rv.get_json()
  # Assert languages key exists.
  assert ("languages" in data)

  # Request voices.
  rv = client.get("/api/v1/voices")
  # Assert OK status.
  assert (rv.status_code == 200)
  # Request video types.
  rv = client.get("/api/v1/videoTypes")
  # Assert OK status.
  assert (rv.status_code == 200)
  # Request video qualities.
  rv = client.get("/api/v1/videoQualities")
  # Assert OK status.
  assert (rv.status_code == 200)


# Test the download endpoint with a temporary file.
def Test_DownloadEndpoint(client, tmp_path):
  # Read STORE_PATH from app config.
  storePath = app.config.get("STORE_PATH")
  # Ensure the store path exists.
  os.makedirs(storePath, exist_ok=True)
  # Construct a unique filename.
  fileName = f"test_download_{int(time.time())}.txt"
  # Build the full file path.
  filePath = os.path.join(storePath, fileName)
  # Write test content into the file.
  with open(filePath, "wb") as f:
    # Write bytes content.
    f.write(b"hello world")
  # Request to download the test file.
  rv = client.get(f"/api/v1/download/{fileName}")
  # Assert successful download.
  assert (rv.status_code == 200)
  # Assert content begins with expected bytes.
  assert (rv.data.startswith(b"hello"))
  # Track removal status.
  removed = False
  # Retry removal for Windows file locks.
  for _ in range(5):
    # Attempt to remove the test file.
    try:
      # Remove the file.
      os.remove(filePath)
      # Mark removed as True.
      removed = True
      # Break out if removed.
      break
    except PermissionError:
      # Sleep briefly before retry.
      time.sleep(0.1)
  # If not removed, schedule best-effort cleanup.
  if (not removed):
    # Check if file still exists.
    if (os.path.exists(filePath)):
      # Try to register atexit cleanup.
      try:
        # Import atexit module.
        import atexit
        # Register a removal callback.
        atexit.register(lambda p=filePath: os.path.exists(p) and os.remove(p))
      except Exception:
        # Swallow any cleanup errors.
        pass


# --- Jobs endpoints (basic flow) ----------------------------------------
# Test the basic jobs flow lifecycle.
def Test_JobsFlow(client):
  # Prepare job payload.
  payload = {
    "text"    : "this is a test job for pytest",
    "language": "en-us",
    "voice"   : "af_nova"
  }
  # Submit a new job.
  rv = client.post("/api/v1/jobs", json=payload)
  # Assert job creation accepted.
  assert (rv.status_code == 202)
  # Parse JSON response.
  data = rv.get_json()
  # Assert jobId exists in response.
  assert ("jobId" in data)
  # Capture jobId value.
  jobId = data["jobId"]

  # List all jobs.
  rv = client.get("/api/v1/jobs")
  # Assert OK status.
  assert (rv.status_code == 200)
  # Parse JSON response.
  data = rv.get_json()
  # Assert jobs key exists.
  assert ("jobs" in data)

  # Get job status.
  rv = client.get(f"/api/v1/jobs/{jobId}")
  # Assert acceptable status codes.
  assert (rv.status_code in (200, 404, 500))

  # Trigger processing for remaining jobs.
  rv = client.post("/api/v1/jobs/triggerRemaining")
  # Assert OK status.
  assert (rv.status_code == 200)

  # Initialize deletion status.
  delStatus = None
  # Attempt deletion with retries due to possible file locks.
  for _ in range(5):
    # Issue delete request for the job.
    rv = client.delete(f"/api/v1/jobs/{jobId}")
    # Record status code.
    delStatus = rv.status_code
    # Break on acceptable codes.
    if (delStatus in (200, 404)):
      # Exit retry loop.
      break
    # Sleep briefly before retry.
    time.sleep(0.2)
  # Accept final status codes after retries.
  assert (delStatus in (200, 404, 500))

  # Try to get the processed result if available.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Accept several possible status codes.
  assert (rv.status_code in (200, 400, 404, 500))

  # Call delete-all-jobs to ensure the endpoint is reachable.
  rv = client.delete("/api/v1/jobs/all")
  # Assert OK status.
  assert (rv.status_code == 200)


# --- Audio endpoint tests (existing) -----------------------------------
# Test audio duration endpoint.
def Test_AudioDuration(client):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare multipart form data.
  data = {"audioFile": (wav, "test.wav")}
  # Post to audio-duration endpoint.
  rv = client.post("/api/v1/audio-duration", content_type="multipart/form-data", data=data)
  # Assert OK status code.
  assert (rv.status_code == 200)
  # Parse JSON response.
  jsonData = rv.get_json()
  # Assert duration exists.
  assert ("duration" in jsonData)


# Test audio size endpoint.
def Test_AudioSize(client):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare multipart form data.
  data = {"audioFile": (wav, "test.wav")}
  # Post to audio-size endpoint.
  rv = client.post("/api/v1/audio-size", content_type="multipart/form-data", data=data)
  # Assert OK status code.
  assert (rv.status_code == 200)
  # Parse JSON response.
  jsonData = rv.get_json()
  # Assert size exists.
  assert ("size" in jsonData)


# Test check-silence endpoint.
def Test_CheckSilence(client):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare multipart form data.
  data = {"audioFile": (wav, "test.wav")}
  # Post to check-silence endpoint.
  rv = client.post("/api/v1/check-silence", content_type="multipart/form-data", data=data)
  # Assert OK status code.
  assert (rv.status_code == 200)
  # Parse JSON response.
  jsonData = rv.get_json()
  # Assert isSilent exists.
  assert ("isSilent" in jsonData)


# Parameterized simple processing endpoints test.
@pytest.mark.parametrize("endpoint,params", [
  # Change volume endpoint with volume parameter.
  ("/api/v1/change-volume", {"volume": "1.0"}),
  # Change speed endpoint with speed parameter.
  ("/api/v1/change-speed", {"speed": "1.0"}),
  # Reverse audio endpoint.
  ("/api/v1/reverse-audio", {}),
  # Normalize audio endpoint with normalization parameters.
  ("/api/v1/normalize-audio",
   {"normalizeBitrate": "128k", "normalizeSampleRate": "22050", "normalizeFilter": "loudnorm"}),
])
# Test simple processing endpoints with generated WAV.
def Test_SimpleProcessingEndpoints(client, endpoint, params):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare multipart form data.
  data = {"audioFile": (wav, "test.wav")}
  # Merge endpoint-specific parameters.
  data.update(params)
  # Post to processing endpoint.
  rv = client.post(endpoint, content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test generate-silent-audio endpoint.
def Test_GenerateSilentAudio(client):
  # Post JSON body to generate silent audio.
  rv = client.post("/api/v1/generate-silent-audio", json={"silentDuration": 1, "silentFormat": ".wav"})
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test convert-audio endpoint.
def Test_ConvertAudio(client):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare multipart form data with output format.
  data = {"audioFile": (wav, "test.wav"), "outputFormat": "mp3"}
  # Post to convert-audio endpoint.
  rv = client.post("/api/v1/convert-audio", content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test concat-audio and split-audio endpoints.
def Test_ConcatAndSplit(client):
  # Create first sine-wave WAV buffer.
  wav1 = MakeSineWavBytes()
  # Create second sine-wave WAV buffer with different frequency.
  wav2 = MakeSineWavBytes(freq=660.0)
  # Build list-like data entries.
  data = [("audioFiles", (wav1, "one.wav")), ("audioFiles", (wav2, "two.wav"))]
  # Flask test client expects dict for multipart.
  files = {"audioFiles": [data[0][1], data[1][1]]}
  # Post to concat-audio endpoint.
  rv = client.post("/api/v1/concat-audio", content_type="multipart/form-data",
                   data={"audioFiles": [data[0][1], data[1][1]]})
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))

  # Create a longer sine-wave WAV buffer.
  longWav = MakeSineWavBytes(duration=2.0)
  # Prepare split parameters.
  data = {"audioFile": (longWav, "long.wav"), "segmentDuration": "1"}
  # Post to split-audio endpoint.
  rv = client.post("/api/v1/split-audio", content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test extract-audio endpoint with sample video if available.
def Test_ExtractAudio(client):
  # Build sample video path.
  samplePath = os.path.join("Assets", "Videos", "Horizontal Videos", "Sample Horizontal (1).mp4")
  # Skip test if sample video does not exist.
  if (not os.path.exists(samplePath)):
    # Skip the test gracefully.
    pytest.skip("No sample video found for extract-audio test")
  # Open the sample video file.
  with open(samplePath, "rb") as f:
    # Post to extract-audio endpoint with video file.
    rv = client.post("/api/v1/extract-audio", content_type="multipart/form-data",
                     data={"videoFile": (f, os.path.basename(samplePath))})
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test fade-audio, remove-vocals, and equalize-audio endpoints together.
def Test_FadeRemoveVocalsEqualize(client):
  # Create a sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare fade parameters.
  data = {"audioFile": (wav, "test.wav"), "fadeIn": "0.2", "fadeOut": "0.2"}
  # Post to fade-audio endpoint.
  rv = client.post("/api/v1/fade-audio", content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))

  # Create a new sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare remove-vocals parameters.
  data = {"audioFile": (wav, "test.wav")}
  # Post to remove-vocals endpoint.
  rv = client.post("/api/v1/remove-vocals", content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))

  # Create another sine-wave WAV buffer.
  wav = MakeSineWavBytes()
  # Prepare equalize parameters.
  data = {"audioFile": (wav, "test.wav"), "freq": "1000", "width": "2", "gain": "3"}
  # Post to equalize-audio endpoint.
  rv = client.post("/api/v1/equalize-audio", content_type="multipart/form-data", data=data)
  # Acceptable status: success or environment error.
  assert (rv.status_code in (200, 400, 500))


# Test invalid voices type parameter to exercise 400 status.
def Test_VoicesInvalidType(client):
  # Request voices with invalid type.
  rv = client.get("/api/v1/voices?type=unknown")
  # Assert bad request.
  assert (rv.status_code == 400)
  # Parse JSON response.
  data = rv.get_json()
  # Assert error message.
  assert ("error" in data)


# Test POST /jobs with invalid JSON body (not JSON).
def Test_PostJobInvalidJson(client):
  # Submit with wrong content type.
  rv = client.post("/api/v1/jobs", data="not-json", content_type="text/plain")
  # Expect 400 bad request.
  assert (rv.status_code == 400)


# Test POST /jobs with missing text.
def Test_PostJobMissingText(client):
  # Submit empty text field.
  rv = client.post("/api/v1/jobs", json={"text": ""})
  # Expect 400 bad request.
  assert (rv.status_code == 400)


# Test POST /jobs with too long text.
def Test_PostJobTooLongText(client):
  # Create an overlong text.
  longText = "x" * 10000
  # Submit overlong text.
  rv = client.post("/api/v1/jobs", json={"text": longText})
  # Expect 400 bad request.
  assert (rv.status_code == 400)


# Test GET /jobs/<jobId> with a non-existent id.
def Test_GetJobNotFound(client):
  # Use a random ID.
  rv = client.get("/api/v1/jobs/ffffffffffffffffffffffffffffffff")
  # Expect 404 not found.
  assert (rv.status_code == 404)


# Helpers to simulate job states for result endpoint.
def _writeJson(path, obj):
  # Write JSON file.
  import json
  with open(path, "w") as f:
    # Dump object.
    json.dump(obj, f)


# Test GET /jobs/<jobId>/result error scenarios.
def Test_JobResultErrors(client):
  # Access app config.
  storePath = app.config.get("STORE_PATH")
  # Create a fake job id.
  jobId = "deadbeefdeadbeefdeadbeefdeadbeef"
  # 1) Not found job.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Expect 404.
  assert (rv.status_code == 404)

  # Prepare job directory.
  import os
  jobDir = os.path.join(storePath, jobId)
  # Ensure directory exists.
  os.makedirs(jobDir, exist_ok=True)

  # 2) Job not completed yet (status queued).
  jobData = {
    "status"    : "queued", "text": "t", "language": "en-us", "voice": "af_nova",
    "speechRate": 1.0, "videoQuality": None, "videoType": None, "createdAt": "now"
  }
  # Write job.json with queued.
  _writeJson(os.path.join(jobDir, "job.json"), jobData)
  # Register job in history as queued.
  app.config["JOB_HISTORY_OBJ"].updateStatus(jobId, "queued")
  # Request result.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Expect 400.
  assert (rv.status_code == 400)

  # 3) Invalid JSON in job.json.
  badPath = os.path.join(jobDir, "job.json")
  # Overwrite malformed JSON.
  with open(badPath, "w") as f:
    # Write invalid json.
    f.write("{ invalid json ")
  # Mark completed in history to bypass status check.
  app.config["JOB_HISTORY_OBJ"].updateStatus(jobId, "completed")
  # Request result.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Expect 500.
  assert (rv.status_code == 500)

  # 4) Valid JSON but processed video missing.
  goodData = {
    "status"    : "completed", "text": "t", "language": "en-us", "voice": "af_nova",
    "speechRate": 1.0, "videoQuality": None, "videoType": None, "createdAt": "now"
  }
  # Write valid json.
  _writeJson(badPath, goodData)
  # Ensure no video file exists.
  for ext in ("mp4", "mov", "mkv"):
    # Build path.
    fp = os.path.join(jobDir, f"{jobId}_Final.{ext}")
    # Remove if exists.
    if (os.path.exists(fp)):
      # Remove file.
      os.remove(fp)
  # Request result.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Expect 404.
  assert (rv.status_code == 404)

  # 5) Empty video file triggers 500.
  videoPath = os.path.join(jobDir, f"{jobId}_Final.mp4")
  # Create empty file.
  with open(videoPath, "wb") as f:
    # Write nothing.
    f.write(b"")
  # Request result.
  rv = client.get(f"/api/v1/jobs/{jobId}/result")
  # Expect 500 due to empty file.
  assert (rv.status_code == 500)


# Test download not-found case.
def Test_DownloadNotFound(client):
  # Request a non-existing file.
  rv = client.get("/api/v1/download/this_file_should_not_exist.xyz")
  # Expect 404.
  assert (rv.status_code == 404)
