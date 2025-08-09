'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Jun 2025
# Last Modification Date: Aug 5th, 2025
# Permissions and Citation: Refer to the README file.
'''

# Suppress warnings from torch and other libraries to keep the output clean.
import shutup

shutup.please()  # This function call suppresses unnecessary warnings.

# Import necessary libraries for the Flask server, file handling, and processing.
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.exceptions import NotFound, BadRequest
import os, yaml, asyncio, hashlib, json, threading, time, logging
from WebHelpers import *
from VideoCreatorHelper import VideoCreatorHelper
from TextToSpeechHelper import TextToSpeechHelper


# Function to process the job in a separate thread.
def ProcessJob(jobId):
  '''Process the job: convert text to speech, add captions, and generate video.'''
  global JOB_HISTORY_OBJ, videoCreator

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


  except Exception as e:
    # If an error occurs, update the job status to "failed".
    if (VERBOSE):
      print(f"Error processing job {jobId}: {str(e)}")
    JOB_HISTORY_OBJ.updateStatus(jobId, "failed")
    UpdateJobStatus(jobId, "failed")
    return jsonify({"error": f"Failed to process job {jobId}: {str(e)}"}), 500


# Function to update the job status in the JSON file.
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

# Initialize the video creator helper.
videoCreator = None

# Initialize the queue watcher thread to monitor job statuses.
# Start the queue watcher thread to monitor job statuses.
QUEUE_WATCHER = QueueWatcher(ProcessJob, maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
# Global dictionary to track job statuses.
JOB_HISTORY_OBJ = QUEUE_WATCHER.jobHistoryObj

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application instance.
app = Flask(__name__)

# Set the secret key for the Flask app to enable session management.
app.secret_key = configs.get("secret", "default_secret_key")


# Routes for web UI.
@app.route("/")
def index():
  return render_template("index.html")


@app.route("/jobs")
def jobsPage():
  return render_template("jobs.html")


# Define a route to get the status of the server.
@app.route(f"/api/v1/status", methods=["GET"])
def getServerStatus():
  '''Return the status of the server to indicate if it is running.'''
  # Return a JSON response indicating the server is running.
  return jsonify({"status": "Server is running"}), 200


# Define a route to get if the server is ready (no jobs in progress).
@app.route(f"/api/v1/ready", methods=["GET"])
def getServerReady():
  '''Check if the server is ready to accept new jobs by verifying job queue capacity.'''
  global JOB_HISTORY_OBJ

  # Count the number of queued jobs to determine server availability.
  noOfQuestedJobs = len([status for status in JOB_HISTORY_OBJ.values() if (status == "queued")])
  isBusy = noOfQuestedJobs >= MAX_JOBS
  if (not isBusy):
    # Return success response when server can accept new jobs.
    return jsonify({"ready": True}), 200
  else:
    # Return not ready response with job count when server is at capacity.
    return jsonify({"ready": False, "jobsInProgress": len(JOB_HISTORY_OBJ)}), 503


@app.route(f"/api/v1/languages", methods=["GET"])
def getAvailableLanguages():
  '''Return a list of available languages for text-to-speech processing.'''
  languages = TextToSpeechHelper().GetAvailableLanguages()

  # Return the list of languages as a JSON response.
  return jsonify({"languages": languages}), 200


@app.route(f"/api/v1/videoTypes", methods=["GET"])
def getAvailableVideoTypes():
  '''Return a list of available video types for video generation.'''
  videoTypes = configs["video"].get("availableTypes", ["Horizontal", "Vertical"])

  # Return the list of video types as a JSON response.
  return jsonify({"videoTypes": videoTypes}), 200


@app.route(f"/api/v1/videoQualities", methods=["GET"])
def getAvailableVideoQualities():
  '''Return a list of available video qualities for video generation.'''
  videoQualities = configs["video"].get("availableQualities", [])

  # Return the list of video qualities as a JSON response.
  return jsonify({"videoQualities": videoQualities}), 200


@app.route(f"/api/v1/voices", methods=["GET"])
def getAvailableVoices():
  '''Return a list of available voices for text-to-speech processing.'''
  # Get the list of available voices from the configuration.
  # Get an attribute from the query.
  typeKey = request.args.get("type", "list").lower()
  if (typeKey not in ["list", "dict"]):
    return jsonify({"error": "Invalid type parameter, must be 'list' or 'dict'"}), 400
  # Get the list of available languages from the configuration.
  if (typeKey == "dict"):
    voices = TextToSpeechHelper().GetAvailableVoicesByLanguage()
  else:
    voices = TextToSpeechHelper().GetAvailableVoices()

  # Return the list of voices as a JSON response.
  return jsonify({"voices": voices}), 200


@app.route(f"/api/v1/jobs", methods=["GET"])
def getAllJobs():
  '''Return a list of all jobs with their statuses.'''
  global JOB_HISTORY_OBJ

  # Prepare a list to hold job details.
  jobsList = []

  # Iterate through the job statuses and collect details.
  for jobId, status in JOB_HISTORY_OBJ.items():
    jobDir = os.path.join(STORE_PATH, jobId)
    jobFilePath = os.path.join(jobDir, "job.json")
    if (os.path.exists(jobFilePath)):
      try:
        with open(jobFilePath, "r") as f:
          jobData = json.load(f)
        jobsList.append({
          "jobId"       : jobId,
          "status"      : status,
          "text"        : jobData.get("text", ""),
          "language"    : jobData.get("language", configs["tts"]["language"]),
          "voice"       : jobData.get("voice", configs["tts"]["voice"]),
          "speechRate"  : jobData.get("speechRate", configs["tts"]["speechRate"]),
          "videoQuality": jobData.get("videoQuality", None),
          "videoType"   : jobData.get("videoType", None),
          "createdAt"   : jobData.get("createdAt", "N/A"),
          "isCompleted" : (status == "completed"),
        })
      except Exception as e:
        if (VERBOSE):
          print(f"Error reading job {jobId}: {str(e)}")

  # Return the list of jobs as a JSON response.
  return jsonify({"jobs": jobsList}), 200


# Define a route to post a job.
@app.route(f"/api/v1/jobs", methods=["POST"])
def postJob():
  '''Create a new job for speech processing and return a unique ID for tracking.'''
  global QUEUE_WATCHER, JOB_HISTORY_OBJ

  # Check if the request contains JSON data.
  if (not request.is_json):
    return jsonify({"error": "Request must be JSON"}), 400

  data = request.get_json()
  if (not data):
    return jsonify({"error": "Invalid JSON data"}), 400

  text = request.json.get("text", "").strip()

  # Validate the input text to ensure it meets requirements.
  if (not text):
    return jsonify({"error": "Text is required"}), 400
  maxTextLength = configs["api"].get("maxTextLength", 2500)
  if (len(text) > maxTextLength):
    return jsonify({"error": f"Text exceeds maximum length of {maxTextLength} characters"}), 400

  # If the server is ready, proceed to create a new job.
  if (VERBOSE):
    print(f"Creating a new job with text: {text[:50]}...")  # Log the first 50 characters of the text.

  # Ensure the jobs directory exists.
  os.makedirs(STORE_PATH, exist_ok=True)

  # Generate a unique ID for the job using MD5 hash of text and timestamp.
  currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  jobId = str(hashlib.md5(text.encode() + currentTime.encode()).hexdigest())

  # Create a directory for the job's files.
  jobDir = os.path.join(STORE_PATH, jobId)
  os.makedirs(jobDir, exist_ok=True)

  # Initialize the queue watcher if not already running.
  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER = QueueWatcher(ProcessJob, maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ

  # Save the initial job status as "queued".
  JOB_HISTORY_OBJ.updateStatus(jobId, "queued")

  # Save the job details to a JSON file.
  jobData = {
    "id"          : jobId,  # Unique identifier for the job.
    "status"      : "queued",  # Initial status of the job.
    "text"        : text,  # Get the text from the request.
    "speechRate"  : request.json.get("speechRate", configs["tts"]["speechRate"]),  # Speech rate for TTS.
    "language"    : request.json.get("language", configs["tts"]["language"]),  # Language for TTS.
    "voice"       : request.json.get("voice", configs["tts"]["voice"]),  # Voice for TTS.
    "videoQuality": request.json.get("videoQuality", None),  # Video quality preference.
    "videoType"   : request.json.get("videoType", None),  # Video type preference.
    "createdAt"   : currentTime,  # Timestamp when the job was created.
  }
  with open(os.path.join(jobDir, "job.json"), "w") as f:
    json.dump(jobData, f)

  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER.start()
  else:
    if (VERBOSE):
      print("Queue watcher is already running or not initialized.")

  # Return the unique job ID with HTTP 202 Accepted status.
  return jsonify({"jobId": jobId}), 202


# Define a route to get the status of a specific job.
@app.route(f"/api/v1/jobs/<jobId>", methods=["GET"])
def getJobStatus(jobId):
  '''Return the status of a specific job identified by its unique job ID.'''
  global JOB_HISTORY_OBJ

  # Check if the job exists in the global status tracking dictionary.
  if (jobId not in JOB_HISTORY_OBJ.keys()):
    return jsonify({"error": "Job not found"}), 404

  # Get the current status of the job.
  status = JOB_HISTORY_OBJ.get(jobId, "unknown")

  # Read the job data from the JSON file.
  jobDir = os.path.join(STORE_PATH, jobId)
  try:
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return jsonify({"error": "Job data not found"}), 404

  # Return the job status and other details.
  return jsonify({
    "jobId"       : jobId,
    "status"      : status,
    "text"        : jobData.get("text", ""),
    "language"    : jobData.get("language", configs["tts"]["language"]),
    "voice"       : jobData.get("voice", configs["tts"]["voice"]),
    "speechRate"  : jobData.get("speechRate", configs["tts"]["speechRate"]),
    "videoQuality": jobData.get("videoQuality", None),
    "videoType"   : jobData.get("videoType", None),
    "createdAt"   : jobData.get("createdAt", "N/A"),
  }), 200


# Define a route to get the processed video.
@app.route("/api/v1/jobs/triggerRemaining", methods=["POST"])
def triggerRemainingJobs():
  '''
  Trigger processing for any remaining queued jobs.
  '''
  global QUEUE_WATCHER, JOB_HISTORY_OBJ

  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER = QueueWatcher(ProcessJob, maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ
    QUEUE_WATCHER.start()
    return jsonify({"message": "Triggered processing for remaining queued jobs."}), 200
  elif (QUEUE_WATCHER and QUEUE_WATCHER.is_alive()):
    return jsonify({"message": "Queue watcher is already running."}), 200
  elif (not QUEUE_WATCHER):
    QUEUE_WATCHER = QueueWatcher(ProcessJob, maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ
    QUEUE_WATCHER.start()
    return jsonify({"message": "Initialized and started queue watcher."}), 200
  else:
    return jsonify({"message": "Queue watcher is already running or not initialized."}), 200


@app.route("/api/v1/jobs/<jobId>/result", methods=["GET"])
def getProcessedVideo(jobId):
  '''
  Return the processed video file for a completed job.
  '''
  # Check if the job exists in the global status tracking dictionary.
  if (jobId not in JOB_HISTORY_OBJ.keys()):
    logger.warning(f"Job {jobId} not found in the jobs.")
    return jsonify({"error": "Job not found"}), 404

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Read the job data from the JSON file.
  jobDataPath = os.path.join(jobDir, "job.json")
  try:
    with open(jobDataPath, "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    logger.error(f"Job data file not found for job {jobId}: {jobDataPath}")
    return jsonify({"error": "Job data not found"}), 404
  except json.JSONDecodeError:
    logger.error(f"Invalid JSON in job data file for job {jobId}: {jobDataPath}")
    return jsonify({"error": "Invalid job data format"}), 500

  # Check if the job is completed before attempting to return the video.
  if (jobData.get("status") != "completed"):
    logger.warning(f"Job {jobId} is not completed yet.")
    return jsonify({"error": "Job not completed yet"}), 400

  # Get the path to the processed video.
  videoFormat = configs["ffmpeg"].get("videoFormat", "mp4")  # Default to "mp4"
  outputVideoPath = os.path.join(jobDir, f"{jobId}_Final.{videoFormat}")

  # Check if the video file exists.
  if (not os.path.exists(outputVideoPath)):
    logger.error(f"Processed video not found for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video not found"}), 404

  # Ensure the file is readable and not empty.
  if (not os.access(outputVideoPath, os.R_OK)):
    logger.error(f"Processed video file is not readable for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video file is not accessible"}), 500
  if (os.path.getsize(outputVideoPath) == 0):
    logger.error(f"Processed video file is empty for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video file is empty"}), 500

  # Return the video file as an attachment for download.
  logger.info(f"Returning processed video for job {jobId}: {outputVideoPath}")
  return send_file(outputVideoPath, as_attachment=True), 200


# Define a route to delete the processed video.
@app.route(f"/api/v1/jobs/<jobId>", methods=["DELETE"])
def deleteProcessedVideo(jobId):
  '''Delete the processed video and associated data for a specific job.'''
  global JOB_HISTORY_OBJ

  # Check if the job exists in the global status tracking dictionary.
  if (jobId not in JOB_HISTORY_OBJ.keys()):
    return jsonify({"error": "Job not found"}), 404

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Remove the job directory and all its contents.
  if (os.path.exists(jobDir)):
    import shutil
    shutil.rmtree(jobDir)

  # Remove the job from the status dictionary.
  if (jobId in JOB_HISTORY_OBJ.keys()):
    JOB_HISTORY_OBJ.delete(jobId)

  # Return a success message.
  return jsonify({"message": "Job data deleted successfully"}), 200


# Define a route to delete all processed videos.
@app.route(f"/api/v1/jobs/", methods=["DELETE"])
def deleteAllProcessedVideos():
  '''Delete all processed videos and associated data for all jobs.'''
  global JOB_HISTORY_OBJ

  # Remove all job directories and their contents.
  if (os.path.exists(STORE_PATH)):
    import shutil
    # Remove the inner folders only.
    for item in os.listdir(STORE_PATH):
      itemPath = os.path.join(STORE_PATH, item)
      if (os.path.isdir(itemPath)):
        shutil.rmtree(itemPath)

  # Clear the job statuses dictionary.
  JOB_HISTORY_OBJ.clear()

  # Return a success message.
  return jsonify({"message": "All job data deleted successfully"}), 200


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
