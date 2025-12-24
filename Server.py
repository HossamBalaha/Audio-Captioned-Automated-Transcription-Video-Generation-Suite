'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Permissions and Citation: Refer to the README file.
'''

# Suppress warnings from torch and other libraries to keep the output clean.
try:
  import shutup

  # This function call suppresses unnecessary warnings.
  shutup.please()
except Exception:
  # Optional dependency "shutup" is not installed; continue without suppressing warnings.
  pass

import os

# Ignore TensorFlow warnings if TensorFlow is used in TTS backends.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logs.

# Import necessary libraries.
import os, yaml, json, logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, render_template
from apiRoutes import apiBp
from WebHelpers import *
from routes import webBp
from datetime import datetime
from VideoCreatorHelper import VideoCreatorHelper
from TextToSpeechHelper import TextToSpeechHelper


def ProcessJob(jobId):
  """Process a job by generating speech and video for the provided job ID."""
  # Get the video creator instance from app config if present.
  videoCreator = app.config.get("videoCreator", None)
  # Get the job history object from app config.
  jobHistoryObj = app.config["JOB_HISTORY_OBJ"]

  # Build the job directory path for file operations.
  jobDir = os.path.join(storePath, jobId)

  # Before switching to processing, check cancel flag if present.
  try:
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      preData = json.load(f)
    if (preData.get("cancelRequested", False)):
      jobHistoryObj.updateStatus(jobId, "canceled")
      UpdateJobStatus(jobId, "canceled")
      if (verbose):
        logger.info(f"Job {jobId} was canceled before processing started.")
      return
  except Exception:
    # Ignore errors reading pre-job data and continue.
    pass

  # Mark job as processing in history and persisted store.
  jobHistoryObj.updateStatus(jobId, "processing")
  UpdateJobStatus(jobId, "processing")

  try:
    # Read the job data from the JSON file.
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)

    # Check cancellation again at start of processing.
    if (jobData.get("cancelRequested", False)):
      jobHistoryObj.updateStatus(jobId, "canceled")
      UpdateJobStatus(jobId, "canceled")
      if (verbose):
        logger.info(f"Job {jobId} canceled at processing start.")
      return

    # Extract parameters from the job data with fallbacks to config defaults.
    text = jobData["text"]
    voice = jobData.get("voice", configs["tts"]["voice"])
    language = jobData.get("language", configs["tts"]["language"])
    speechRate = jobData.get("speechRate", configs["tts"]["speechRate"])
    videoQuality = jobData.get("videoQuality", None)
    videoType = jobData.get("videoType", None)

    # Validate language against available TTS languages and fallback to default if unsupported.
    try:
      ttsHelperLocal = TextToSpeechHelper()
      availableLanguages = ttsHelperLocal.GetAvailableLanguages()
      if (language not in availableLanguages):
        language = configs["tts"]["language"]
        if (verbose):
          logger.info("Provided language is unsupported; falling back to default.")
    except Exception:
      # Ignore validation errors and continue with chosen language.
      pass

    # Validate voice against available voices and fallback to default if unsupported.
    try:
      ttsHelperLocal = TextToSpeechHelper()
      availableVoices = ttsHelperLocal.GetAvailableVoices()
      if (((voice is None) or (voice not in availableVoices)) and (len(availableVoices) > 0)):
        voice = configs["tts"]["voice"]
        if (verbose):
          logger.info("Provided voice is unsupported; falling back to default.")
    except Exception:
      # Ignore validation errors and continue with chosen voice.
      pass

    if (verbose):
      logger.info(
        f"Processing job {jobId} with language: {language}, "
        f"voice: {voice}, speech rate: {speechRate}, "
        f"video quality: {videoQuality}, video type: {videoType}"
      )
      logger.info(f"Text: {text[:50]}...")

    # Initialize the video creator helper if not already available.
    if (not videoCreator):
      videoCreator = VideoCreatorHelper()

    # Generate a video from the provided text.
    isGenerated, videoID = videoCreator.GenerateVideo(
      text.strip(),
      language=language,
      voice=voice,
      speechRate=speechRate,
      videoQuality=videoQuality,
      videoType=videoType,
      uniqueHashID=jobId,
    )

    if (not isGenerated):
      jobHistoryObj.updateStatus(jobId, "failed")
      UpdateJobStatus(jobId, "failed")
      return jsonify({"error": "Failed to generate video"}), 500

    # Update the job status to completed after successful generation.
    if (verbose):
      logger.info(f"Video generated successfully for job {jobId} with ID: {videoID}")
    jobHistoryObj.updateStatus(jobId, "completed")
    UpdateJobStatus(jobId, "completed")

    # Persist the video creator instance in the app config for reuse.
    app.config["videoCreator"] = videoCreator

  except Exception as e:
    # On any exception during processing, mark job as failed and log the error.
    if (verbose):
      logger.exception(f"Error processing job {jobId}: {str(e)}")
    jobHistoryObj.updateStatus(jobId, "failed")
    UpdateJobStatus(jobId, "failed")
    return jsonify({"error": f"Failed to process job {jobId}: {str(e)}"}), 500


def UpdateJobStatus(jobId, status):
  """Persist the status for a given job ID to its job.json file."""
  # Build job directory and file paths.
  jobDir = os.path.join(storePath, jobId)
  jobFilePath = os.path.join(jobDir, "job.json")

  # Read the existing job data and return if not found.
  try:
    with open(jobFilePath, "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return

  # Update the status and write back the job data.
  jobData["status"] = status
  with open(jobFilePath, "w") as f:
    json.dump(jobData, f)

  if (verbose):
    logger.info(f"Job {jobId} status updated to: {status}")


with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)

# Get the verbose setting from the config.
verbose = configs.get("verbose", False)
# Read port from the nested api config (matches configs.yaml).
port = int(configs.get("api", {}).get("port", 5000))
maxJobs = configs["api"].get("maxJobs", 1)
storePath = configs.get("storePath", "./Jobs")
maxTimeout = configs["api"].get("maxTimeout", 10)

# Configure logging: write logs to a file inside the Logs folder and also to the console.
# This ensures all module loggers that propagate to the root logger will be captured.
logDir = configs.get("logPath", "Logs")
os.makedirs(logDir, exist_ok=True)
timestamp = datetime.now().strftime("%Y_%m_%d")
logFilePath = os.path.join(logDir, f"Server_Log_{timestamp}.log")

# Determine log level from verbose flag.
rootLogLevel = logging.DEBUG if verbose else logging.INFO
rootLogger = logging.getLogger()
rootLogger.setLevel(rootLogLevel)

# Create a formatter used by both handlers.
logFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Add a rotating file handler (avoid adding duplicate handlers on repeated imports).
fileHandlerExists = any(
  getattr(h, "baseFilename", None) == os.path.abspath(logFilePath)
  for h in rootLogger.handlers
)
if (not fileHandlerExists):
  fileHandler = RotatingFileHandler(
    logFilePath,
    maxBytes=int(configs.get("logMaxBytes", 5 * 1024 * 1024)),
    backupCount=int(configs.get("logBackupCount", 5)),
    encoding="utf-8",
  )
  fileHandler.setLevel(rootLogLevel)
  fileHandler.setFormatter(logFormatter)
  rootLogger.addHandler(fileHandler)

# Ensure we have a console/stream handler as well (useful during development).
if (not any(isinstance(h, logging.StreamHandler) for h in rootLogger.handlers)):
  streamHandler = logging.StreamHandler()
  streamHandler.setLevel(rootLogLevel)
  streamHandler.setFormatter(logFormatter)
  rootLogger.addHandler(streamHandler)

# Expose a module logger for Server.py and for storing in app config.
logger = logging.getLogger(__name__)

# Determine test mode from environment or configs.
testMode = (os.environ.get("T2V_TEST_MODE", "0") == "1") or bool(configs.get("testMode", False))
# Initialize the queue watcher thread to monitor job statuses unless in test mode.
if (not testMode):
  queueWatcher = QueueWatcher(ProcessJob, maxJobs=maxJobs, maxTimeout=maxTimeout)
  jobHistoryObj = queueWatcher.jobHistoryObj
else:
  # In test mode, use a lightweight job history object without starting threads.
  queueWatcher = None
  jobHistoryObj = JobStatusHistory()

# Define the directory where job data will be stored.
os.makedirs(storePath, exist_ok=True)

# Create the Flask application and store configuration values in app.config.
app = Flask(__name__)
app.secret_key = configs.get("secret", "default_secret_key")
app.config["STORE_PATH"] = storePath
app.config["JOB_HISTORY_OBJ"] = jobHistoryObj
app.config["configs"] = configs
app.config["MAX_JOBS"] = maxJobs
app.config["MAX_TIMEOUT"] = maxTimeout
app.config["VERBOSE"] = verbose
app.config["QUEUE_WATCHER"] = queueWatcher
app.config["TEST_MODE"] = testMode
app.config["ProcessJob"] = ProcessJob
app.config["logger"] = logger
app.config["videoCreator"] = None

# Register blueprints for API and web routes.
app.register_blueprint(apiBp)
app.register_blueprint(webBp)

# Run the Flask application when this module is executed directly.
if (__name__ == "__main__"):
  # Load the previously saved job statuses if they exist.
  jobsList = os.listdir(storePath)
  # Filter out non-directory entries from jobs list.
  jobsList = [jobId for jobId in jobsList if os.path.isdir(os.path.join(storePath, jobId))]
  for jobId in jobsList:
    jobFilePath = os.path.join(storePath, jobId, "job.json")
    if (os.path.exists(jobFilePath)):
      try:
        with open(jobFilePath, "r") as f:
          jobData = json.load(f)
        jobHistoryObj.updateStatus(jobId, jobData.get("status", "unknown"))
        jobStatus = jobHistoryObj.get(jobId, "unknown")
        if ((jobStatus == "queued") or (jobStatus == "processing")):
          # Convert it to "queued" so it can be reprocessed by the queue watcher.
          jobHistoryObj.updateStatus(jobId, "queued")
          UpdateJobStatus(jobId, "queued")
      except Exception as e:
        if (verbose):
          logger.exception(f"Error loading job {jobId}: {str(e)}")
    else:
      jobHistoryObj.updateStatus(jobId, "unknown")

  if (verbose):
    logger.info(f"Loaded {len(jobHistoryObj)} jobs from the store path: {storePath}")
    for jobId, status in jobHistoryObj.items():
      logger.info(f"Loaded job {jobId} with status: {status}")

  if ((not testMode) and queueWatcher):
    queueWatcher.start()  # Start the queue watcher thread to monitor job statuses.

  # Start the Flask application.
  # If the environment variable T2V_NO_RELOADER is set to "1", disable the reloader so
  # the original process does not exit (useful when launching from a batch file).
  noReloader = os.environ.get("T2V_NO_RELOADER", "0") == "1"
  if (noReloader):
    if (verbose):
      logger.info("Starting Flask without reloader (T2V_NO_RELOADER=1).")
    app.run(
      host="0.0.0.0",
      port=port,
      debug=verbose,
      use_reloader=False,
    )
  else:
    app.run(
      host="0.0.0.0",  # Listen on all interfaces.
      port=port,  # Use the port specified in the configuration.
      debug=verbose,  # Enable debug mode if verbose is set.
      # threaded=True,  # Allow multiple requests to be handled simultaneously.
      # use_reloader=False,  # Disable the reloader to avoid issues with threading.
    )
