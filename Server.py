'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Jun 2025
# Last Modification Date: Aug 4th, 2025
# Permissions and Citation: Refer to the README file.
'''

# Suppress warnings from torch and other libraries to keep the output clean.
import shutup

shutup.please()  # This function call suppresses unnecessary warnings.

# Import necessary libraries for the Flask server, file handling, and processing.
from flask import Flask, request, jsonify, send_file
from flask import render_template
import os, yaml, asyncio, hashlib, json, threading, time
from VideoCreatorHelper import VideoCreatorHelper
from TextToSpeechHelper import TextToSpeechHelper

with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)

# Get the verbose setting from the config.
VERBOSE = configs.get("verbose", False)
PORT = configs.get("port", 5000)
MAX_JOBS = configs["api"].get("maxJobs", 1)
STORE_PATH = configs.get("storePath", "./Jobs")

# Define the directory where job data will be stored.
os.makedirs(STORE_PATH, exist_ok=True)

# Initialize the video creator helper.
videoCreator = None

# Store job statuses in a dictionary for quick access.
# In a production environment, a database would be more appropriate.
JOB_STATUSES = {}

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


# @app.before_request
# def before_request():
#   """Function to run before each request to set up necessary configurations."""
#   # Set the response headers to allow cross-origin requests.
#   if (VERBOSE):
#     print("Setting CORS headers for the request.")
#   request.headers["Access-Control-Allow-Origin"] = "*"
#   request.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
#   request.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

# Define a route to get the status of the server.
@app.route(f"/api/v1/status", methods=["GET"])
def getServerStatus():
  """Return the status of the server to indicate if it is running."""
  # Return a JSON response indicating the server is running.
  return jsonify({"status": "Server is running"}), 200


# Define a route to get if the server is ready (no jobs in progress).
@app.route(f"/api/v1/ready", methods=["GET"])
def getServerReady():
  """Check if the server is ready to accept new jobs by verifying job queue capacity."""
  global JOB_STATUSES

  # Count the number of queued jobs to determine server availability.
  noOfQuestedJobs = len([status for status in JOB_STATUSES.values() if (status == "queued")])
  isBusy = noOfQuestedJobs >= MAX_JOBS
  if (not isBusy):
    # Return success response when server can accept new jobs.
    return jsonify({"ready": True}), 200
  else:
    # Return not ready response with job count when server is at capacity.
    return jsonify({"ready": False, "jobsInProgress": len(JOB_STATUSES)}), 503


@app.route(f"/api/v1/languages", methods=["GET"])
def getAvailableLanguages():
  """Return a list of available languages for text-to-speech processing."""
  languages = TextToSpeechHelper().GetAvailableLanguages()

  # Return the list of languages as a JSON response.
  return jsonify({"languages": languages}), 200


@app.route(f"/api/v1/voices", methods=["GET"])
def getAvailableVoices():
  """Return a list of available voices for text-to-speech processing."""
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
  """Return a list of all jobs with their statuses."""
  global JOB_STATUSES

  # Prepare a list to hold job details.
  jobsList = []

  # Iterate through the job statuses and collect details.
  for jobId, status in JOB_STATUSES.items():
    jobDir = os.path.join(STORE_PATH, jobId)
    jobFilePath = os.path.join(jobDir, "job.json")
    if (os.path.exists(jobFilePath)):
      try:
        with open(jobFilePath, "r") as f:
          jobData = json.load(f)
        jobsList.append({
          "jobId"    : jobId,
          "status"   : status,
          "text"     : jobData.get("text", ""),
          "language" : jobData.get("language", configs["tts"]["language"]),
          "voice"    : jobData.get("voice", configs["tts"]["voice"]),
          "createdAt": jobData.get("createdAt", "N/A"),
          "isCompleted": (status == "completed"),
        })
      except Exception as e:
        if (VERBOSE):
          print(f"Error reading job {jobId}: {str(e)}")

  # Return the list of jobs as a JSON response.
  return jsonify({"jobs": jobsList}), 200


# Define a route to post a job.
@app.route(f"/api/v1/jobs", methods=["POST"])
def postJob():
  """Create a new job for speech processing and return a unique ID for tracking."""
  global JOB_STATUSES

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

  # Check if the server is ready to accept new jobs.
  noOfQuestedJobs = len([status for status in JOB_STATUSES.values() if (status == "queued")])
  isBusy = noOfQuestedJobs >= MAX_JOBS
  if (isBusy):
    return jsonify({"error": "Server is busy, please try again later"}), 503

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

  # Save the initial job status as "queued".
  JOB_STATUSES[jobId] = "queued"

  # Save the job details to a JSON file.
  jobData = {
    "id"       : jobId,  # Unique identifier for the job.
    "status"   : "queued",  # Initial status of the job.
    "text"     : text,  # Get the text from the request.
    "language" : request.json.get("language", configs["tts"]["language"]),  # Language for TTS.
    "voice"    : request.json.get("voice", configs["tts"]["voice"]),  # Voice for TTS.
    "createdAt": currentTime,  # Timestamp when the job was created.
  }
  with open(os.path.join(jobDir, "job.json"), "w") as f:
    json.dump(jobData, f)

  # Start the processing in a separate thread to avoid blocking the request.
  thread = threading.Thread(target=ProcessJob, args=(jobId,))
  thread.start()

  # Return the unique job ID with HTTP 202 Accepted status.
  return jsonify({"jobId": jobId}), 202


# Define a route to get the status of a specific job.
@app.route(f"/api/v1/jobs/<jobId>", methods=["GET"])
def getJobStatus(jobId):
  """Return the status of a specific job identified by its unique job ID."""
  global JOB_STATUSES

  # Check if the job exists in the global status tracking dictionary.
  if (jobId not in JOB_STATUSES):
    return jsonify({"error": "Job not found"}), 404

  # Get the current status of the job.
  status = JOB_STATUSES.get(jobId, "unknown")

  # Read the job data from the JSON file.
  jobDir = os.path.join(STORE_PATH, jobId)
  try:
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return jsonify({"error": "Job data not found"}), 404

  # Return the job status and other details.
  return jsonify({
    "jobId"    : jobId,
    "status"   : status,
    "text"     : jobData.get("text", ""),
    "language" : jobData.get("language", configs["tts"]["language"]),
    "voice"    : jobData.get("voice", configs["tts"]["voice"]),
    "createdAt": jobData.get("createdAt", "N/A"),
  }), 200


# Define a route to get the processed video.
@app.route(f"/api/v1/jobs/<jobId>/result", methods=["GET"])
def getProcessedVideo(jobId):
  """Return the processed video file for a completed job."""
  global JOB_STATUSES

  # Check if the job exists in the global status tracking dictionary.
  if (jobId not in JOB_STATUSES):
    return jsonify({"error": "Job not found"}), 404

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Read the job data from the JSON file.
  try:
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return jsonify({"error": "Job data not found"}), 404

  # Check if the job is completed before attempting to return the video.
  if (jobData["status"] != "completed"):
    return jsonify({"error": "Job not completed yet"}), 400

  # Get the path to the processed video.
  videoFormat = configs["ffmpeg"].get("videoFormat", "mp4")
  outputVideoPath = os.path.join(jobDir, f"{jobId}_Final.{videoFormat}")

  # Check if the video file exists.
  if (not os.path.exists(outputVideoPath)):
    if (VERBOSE):
      print(f"Processed video not found for job {jobId} at path: {outputVideoPath}")
    return jsonify({"error": "Processed video not found"}), 404

  # Return the video file as an attachment for download.
  return send_file(outputVideoPath, as_attachment=True), 200


# Define a route to delete the processed video.
@app.route(f"/api/v1/jobs/<jobId>", methods=["DELETE"])
def deleteProcessedVideo(jobId):
  """Delete the processed video and associated data for a specific job."""
  global JOB_STATUSES

  # Check if the job exists in the global status tracking dictionary.
  if jobId not in JOB_STATUSES:
    return jsonify({"error": "Job not found"}), 404

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Remove the job directory and all its contents.
  if (os.path.exists(jobDir)):
    import shutil
    shutil.rmtree(jobDir)

  # Remove the job from the status dictionary.
  if (jobId in JOB_STATUSES):
    del JOB_STATUSES[jobId]

  # Return a success message.
  return jsonify({"message": "Job data deleted successfully"}), 200


# Define a route to delete all processed videos.
@app.route(f"/api/v1/jobs/", methods=["DELETE"])
def deleteAllProcessedVideos():
  """Delete all processed videos and associated data for all jobs."""
  global JOB_STATUSES

  # Remove all job directories and their contents.
  if (os.path.exists(STORE_PATH)):
    import shutil
    shutil.rmtree(STORE_PATH)

  # Clear the job statuses dictionary.
  JOB_STATUSES.clear()

  # Return a success message.
  return jsonify({"message": "All job data deleted successfully"}), 200


# Function to process the job in a separate thread.
def ProcessJob(jobId):
  """Process the job: convert text to speech, add captions, and generate video."""
  global JOB_STATUSES, videoCreator

  # Get the job directory path for file operations.
  jobDir = os.path.join(STORE_PATH, jobId)

  # Update the job status to "processing".
  JOB_STATUSES[jobId] = "processing"
  UpdateJobStatus(jobId, "processing")

  try:
    # Read the job data from the JSON file.
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)

    # Get the texts and videos from the job data.
    text = jobData["text"]
    voice = jobData.get("voice", configs["tts"]["voice"])
    language = jobData.get("language", configs["tts"]["language"])
    if (VERBOSE):
      print(f"Processing job {jobId} with language: {language}, voice: {voice}")
      print(f"Text: {text[:50]}...")

    if (not videoCreator):
      # Initialize the video creator helper if not already done.
      videoCreator = VideoCreatorHelper()

    # Generate a video from the provided text.
    isGenerated, videoID = videoCreator.GenerateVideo(
      text.strip(),
      language=language,
      voice=voice,
      uniqueHashID=jobId
    )

    if (not isGenerated):
      JOB_STATUSES[jobId] = "failed"
      UpdateJobStatus(jobId, "failed")
      return jsonify({"error": "Failed to generate video"}), 500

    # If the video was generated successfully, update the job status.
    if (VERBOSE):
      print(f"Video generated successfully for job {jobId} with ID: {videoID}")
    JOB_STATUSES[jobId] = "completed"
    UpdateJobStatus(jobId, "completed")


  except Exception as e:
    # If an error occurs, update the job status to "failed".
    if (VERBOSE):
      print(f"Error processing job {jobId}: {str(e)}")
    JOB_STATUSES[jobId] = "failed"
    UpdateJobStatus(jobId, "failed")
    return jsonify({"error": f"Failed to process job {jobId}: {str(e)}"}), 500


# Function to update the job status in the JSON file.
def UpdateJobStatus(jobId, status):
  """Update the job status in the job's JSON file to maintain persistence."""
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


# Run the Flask application.
if __name__ == "__main__":
  with app.app_context():
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
          JOB_STATUSES[jobId] = jobData.get("status", "unknown")
          jobStatus = JOB_STATUSES[jobId]
          if ((jobStatus == "queued") or (jobStatus == "processing")):
            # Convert it to "failed" if it was processing when the server started.
            JOB_STATUSES[jobId] = "failed"
            UpdateJobStatus(jobId, "failed")
        except Exception as e:
          if (VERBOSE):
            print(f"Error loading job {jobId}: {str(e)}")
      else:
        JOB_STATUSES[jobId] = "unknown"

    for jobId, status in JOB_STATUSES.items():
      if (VERBOSE):
        print(f"Loaded job {jobId} with status: {status}")

    app.run(
      host="0.0.0.0",  # Listen on all interfaces.
      port=PORT,  # Use the port specified in the configuration.
      debug=VERBOSE,  # Enable debug mode if verbose is set.
      # threaded=True,  # Allow multiple requests to be handled simultaneously.
      # use_reloader=False,  # Disable the reloader to avoid issues with threading.
    )
