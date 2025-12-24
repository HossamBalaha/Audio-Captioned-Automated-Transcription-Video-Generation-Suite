import os, json, sys, pytest, yaml
from flask import Flask

# Ensure Windows paths work.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if (ROOT not in sys.path):
  sys.path.insert(0, ROOT)
os.chdir(ROOT)

# Import the Flask app from Server.
from Server import app as flaskApp


@pytest.fixture(scope="module")
def client():
  """Provide a Flask test client for API endpoint tests."""
  flaskApp.config.update({
    "TESTING": True,
  })
  with flaskApp.test_client() as c:
    yield c


def CreateJob(client, text="Hello from test", language="en", voice="default"):
  """Helper to create a job and return jobId."""
  rv = client.post("/api/v1/jobs", json={
    "text"        : text,
    "language"    : language,
    "voice"       : voice,
    "videoQuality": "Full HD",
    "videoType"   : "Horizontal",
  })
  assert rv.status_code in (202, 200)
  data = rv.get_json()
  assert "jobId" in data
  return data["jobId"]


def Test_JobsPagination(client):
  """Jobs list supports pagination and returns shape with total, page, pageSize, jobs."""
  # Create a couple of jobs.
  jid1 = CreateJob(client, text="Job One")
  jid2 = CreateJob(client, text="Job Two")
  rv = client.get("/api/v1/jobs?page=1&pageSize=1")
  assert rv.status_code == 200
  data = rv.get_json()
  assert "total" in data and "page" in data and "pageSize" in data and "jobs" in data
  assert data["page"] == 1
  assert data["pageSize"] == 1
  assert isinstance(data["jobs"], list)


def Test_JobMetadataDownload(client):
  """Metadata endpoint returns the job.json file."""
  jid = CreateJob(client, text="Meta Test")
  rv = client.get(f"/api/v1/jobs/{jid}/metadata")
  # send_file returns status 200 and data is file-like; we check status only here.
  assert rv.status_code == 200


def Test_JobCancelAndRetry(client):
  """Cancel a queued job, then retry it and check retries increment."""
  jid = CreateJob(client, text="Cancel Retry Test")
  # Cancel.
  rv = client.delete(f"/api/v1/jobs/{jid}/cancel")
  assert rv.status_code in (200, 202)
  # Retry.
  rv = client.post(f"/api/v1/jobs/{jid}/retry")
  assert rv.status_code == 200
  data = rv.get_json()
  assert "retries" in data and isinstance(data["retries"], int)


def Test_StatusEndpoint(client):
  """Status endpoint returns ffmpeg availability and store writability."""
  rv = client.get("/api/v1/status")
  assert rv.status_code == 200
  data = rv.get_json()
  assert "ffmpegAvailable" in data
  assert "storeWritable" in data


def Test_JobResultDownload(client):
  """Simulate a completed job and verify the result download endpoint returns the file."""
  # Create a job normally to get structure.
  jid = CreateJob(client, text="Result Test")
  # Read configs to discover store path and video format.
  with open(os.path.join(ROOT, "configs.yaml"), "r") as cf:
    configs = yaml.safe_load(cf)
  storePath = configs.get("storePath", "./Jobs")
  videoFormat = configs.get("ffmpeg", {}).get("videoFormat", "mp4")
  jobDir = os.path.join(storePath, jid)
  os.makedirs(jobDir, exist_ok=True)
  # Update job.json to completed status.
  jobJsonPath = os.path.join(jobDir, "job.json")
  try:
    with open(jobJsonPath, "r") as jf:
      jobData = json.load(jf)
  except Exception:
    jobData = {"id": jid, "text": "Result Test"}
  jobData["status"] = "completed"
  with open(jobJsonPath, "w") as jf:
    json.dump(jobData, jf)
  # Create a small dummy final video file.
  finalPath = os.path.join(jobDir, f"{jid}_Final.{videoFormat}")
  with open(finalPath, "wb") as f:
    f.write(b"00")  # Non-empty content.
  # Request the result download.
  rv = client.get(f"/api/v1/jobs/{jid}/result")
  assert rv.status_code == 200
