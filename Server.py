'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Jun 2025
# Last Modification Date: Aug 18th, 2025
# Permissions and Citation: Refer to the README file.
'''

# Suppress warnings from torch and other libraries to keep the output clean.
import shutup

# This function call suppresses unnecessary warnings.
shutup.please()

# Import necessary libraries.
import os, yaml, json, threading, logging
from flask import Flask, request, jsonify, render_template
from apiRoutes import apiBp
from routes import webBp
from WebHelpers import *
from VideoCreatorHelper import VideoCreatorHelper


def ProcessJob(jobId):
  '''Process the job: convert text to speech, add captions, and generate video.'''
  videoCreator = app.config.get("videoCreator", None)
  JOB_HISTORY_OBJ = app.config["JOB_HISTORY_OBJ"]

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Update the job status to "processing".
  JOB_HISTORY_OBJ.updateStatus(jobId, "processing")
  UpdateJobStatus(jobId, "processing")

  try:
    # Read the job data from the JSON file.
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)

    # Get the texts and videos from the job data.
    text = jobData["text"]
    voice = jobData.get("voice", configs["tts"]["voice"])
    language = jobData.get("language", configs["tts"]["language"])
    speechRate = jobData.get("speechRate", configs["tts"]["speechRate"])
    videoQuality = jobData.get("videoQuality", None)
    videoType = jobData.get("videoType", None)

    if (VERBOSE):
      print(
        f"Processing job {jobId} with language: {language}, "
        f"voice: {voice}, speech rate: {speechRate}, "
        f"video quality: {videoQuality}, video type: {videoType}"
      )
      print(f"Text: {text[:50]}...")

    if (not videoCreator):
      # Initialize the video creator helper if not already done.
      videoCreator = VideoCreatorHelper()

    # Generate a video from the provided text.
    isGenerated, videoID = videoCreator.GenerateVideo(
      text.strip(),
      language=language,
      voice=voice,
      speechRate=speechRate,
      videoQuality=videoQuality,
      videoType=videoType,
      uniqueHashID=jobId
    )

    if (not isGenerated):
      JOB_HISTORY_OBJ.updateStatus(jobId, "failed")
      UpdateJobStatus(jobId, "failed")
      return jsonify({"error": "Failed to generate video"}), 500

    # If the video was generated successfully, update the job status.
    if (VERBOSE):
      print(f"Video generated successfully for job {jobId} with ID: {videoID}")
    JOB_HISTORY_OBJ.updateStatus(jobId, "completed")
    UpdateJobStatus(jobId, "completed")

    # Update the video creator in the app config.
    app.config["videoCreator"] = videoCreator

  except Exception as e:
    # If an error occurs, update the job status to "failed".
    if (VERBOSE):
      print(f"Error processing job {jobId}: {str(e)}")
    JOB_HISTORY_OBJ.updateStatus(jobId, "failed")
    UpdateJobStatus(jobId, "failed")
    return jsonify({"error": f"Failed to process job {jobId}: {str(e)}"}), 500


def UpdateJobStatus(jobId, status):
  '''Update the job status in the job's JSON file to maintain persistence.'''
  jobDir = os.path.join(STORE_PATH, jobId)
  jobFilePath = os.path.join(jobDir, "job.json")

  # Read the existing job data.
  try:
    with open(jobFilePath, "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return

  # Update the status in the job data.
  jobData["status"] = status

  # Write the updated job data back to the JSON file.
  with open(jobFilePath, "w") as f:
    json.dump(jobData, f)

  if (VERBOSE):
    print(f"Job {jobId} status updated to: {status}")


with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)

# Get the verbose setting from the config.
VERBOSE = configs.get("verbose", False)
PORT = configs.get("port", 5000)
MAX_JOBS = configs["api"].get("maxJobs", 1)
STORE_PATH = configs.get("storePath", "./Jobs")
MAX_TIMEOUT = configs["api"].get("maxTimeout", 10)

# Define the directory where job data will be stored.
os.makedirs(STORE_PATH, exist_ok=True)

# Initialize the queue watcher thread to monitor job statuses.
# Start the queue watcher thread to monitor job statuses.
QUEUE_WATCHER = QueueWatcher(ProcessJob, maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
# Global dictionary to track job statuses.
JOB_HISTORY_OBJ = QUEUE_WATCHER.jobHistoryObj

# Configure logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application instance.
app = Flask(__name__)
app.secret_key = configs.get("secret", "default_secret_key")
app.config["STORE_PATH"] = STORE_PATH
app.config["JOB_HISTORY_OBJ"] = JOB_HISTORY_OBJ
app.config["configs"] = configs
app.config["MAX_JOBS"] = MAX_JOBS
app.config["MAX_TIMEOUT"] = MAX_TIMEOUT
app.config["VERBOSE"] = VERBOSE
app.config["QUEUE_WATCHER"] = QUEUE_WATCHER
app.config["ProcessJob"] = ProcessJob
app.config["logger"] = logger
app.config["videoCreator"] = None

app.register_blueprint(apiBp)
app.register_blueprint(webBp)

# Run the Flask application.
if __name__ == "__main__":
  # with app.app_context():
  # Load the previously saved job statuses if they exist.
  jobsList = os.listdir(STORE_PATH)
  # Check if it is a directory and filter out any non-directory entries.
  jobsList = [jobId for jobId in jobsList if os.path.isdir(os.path.join(STORE_PATH, jobId))]
  for jobId in jobsList:
    jobFilePath = os.path.join(STORE_PATH, jobId, "job.json")
    if (os.path.exists(jobFilePath)):
      try:
        with open(jobFilePath, "r") as f:
          jobData = json.load(f)
        JOB_HISTORY_OBJ.updateStatus(jobId, jobData.get("status", "unknown"))
        jobStatus = JOB_HISTORY_OBJ.get(jobId, "unknown")
        if ((jobStatus == "queued") or (jobStatus == "processing")):
          # Convert it to "failed" if it was processing when the server started.
          JOB_HISTORY_OBJ.updateStatus(jobId, "queued")
          UpdateJobStatus(jobId, "queued")
      except Exception as e:
        if (VERBOSE):
          print(f"Error loading job {jobId}: {str(e)}")
    else:
      JOB_HISTORY_OBJ.updateStatus(jobId, "unknown")

  if (VERBOSE):
    print(f"Loaded {len(JOB_HISTORY_OBJ)} jobs from the store path: {STORE_PATH}")
    for jobId, status in JOB_HISTORY_OBJ.items():
      print(f"Loaded job {jobId} with status: {status}")

  QUEUE_WATCHER.start()  # Start the queue watcher thread to monitor job statuses.

  # Start the Flask application.
  app.run(
    host="0.0.0.0",  # Listen on all interfaces.
    port=PORT,  # Use the port specified in the configuration.
    debug=VERBOSE,  # Enable debug mode if verbose is set.
    # threaded=True,  # Allow multiple requests to be handled simultaneously.
    # use_reloader=False,  # Disable the reloader to avoid issues with threading.
  )
