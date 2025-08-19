'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Aug 2025
# Last Modification Date: Aug 18th, 2025
# Permissions and Citation: Refer to the README file.
'''

import os, json, time, hashlib, asyncio
from flask import Blueprint, jsonify, current_app, request, send_file
from WebHelpers import *
from TextToSpeechHelper import TextToSpeechHelper
from FFMPEGHelper import FFMPEGHelper

apiBp = Blueprint("api", __name__)


@apiBp.route("/api/v1/status", methods=["GET"])
def getServerStatus():
  return jsonify({"status": "Server is running"}), 200


@apiBp.route("/api/v1/ready", methods=["GET"])
def getServerReady():
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  MAX_JOBS = current_app.config.get("MAX_JOBS", 1)
  noOfQuestedJobs = len([status for status in JOB_HISTORY_OBJ.values() if (status == "queued")])
  isBusy = noOfQuestedJobs >= MAX_JOBS
  if (not isBusy):
    return jsonify({"ready": True}), 200
  else:
    return jsonify({"ready": False, "jobsInProgress": len(JOB_HISTORY_OBJ)}), 503


@apiBp.route("/api/v1/languages", methods=["GET"])
def getAvailableLanguages():
  languages = TextToSpeechHelper().GetAvailableLanguages()
  return jsonify({"languages": languages}), 200


@apiBp.route("/api/v1/videoTypes", methods=["GET"])
def getAvailableVideoTypes():
  configs = current_app.config["configs"]
  videoTypes = configs["video"].get("availableTypes", ["Horizontal", "Vertical"])
  return jsonify({"videoTypes": videoTypes}), 200


@apiBp.route("/api/v1/videoQualities", methods=["GET"])
def getAvailableVideoQualities():
  configs = current_app.config["configs"]
  videoQualities = configs["video"].get("availableQualities", [])
  return jsonify({"videoQualities": videoQualities}), 200


@apiBp.route("/api/v1/voices", methods=["GET"])
def getAvailableVoices():
  typeKey = request.args.get("type", "list").lower()
  if (typeKey not in ["list", "dict"]):
    return jsonify({"error": "Invalid type parameter, must be 'list' or 'dict'"}), 400
  if (typeKey == "dict"):
    voices = TextToSpeechHelper().GetAvailableVoicesByLanguage()
  else:
    voices = TextToSpeechHelper().GetAvailableVoices()
  return jsonify({"voices": voices}), 200


@apiBp.route("/api/v1/jobs", methods=["GET"])
def getAllJobs():
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  STORE_PATH = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]
  jobsList = []
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
        pass
  return jsonify({"jobs": jobsList}), 200


@apiBp.route("/api/v1/jobs", methods=["POST"])
def postJob():
  QUEUE_WATCHER = current_app.config["QUEUE_WATCHER"]
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  STORE_PATH = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]
  VERBOSE = current_app.config.get("VERBOSE", False)
  MAX_JOBS = current_app.config.get("MAX_JOBS", 1)
  MAX_TIMEOUT = current_app.config.get("MAX_TIMEOUT", 10)

  if (not request.is_json):
    return jsonify({"error": "Request must be JSON"}), 400
  data = request.get_json()

  if (not data):
    return jsonify({"error": "Invalid JSON data"}), 400
  text = request.json.get("text", "").strip()
  if (not isinstance(text, str)):
    text = str(text)
  if (not text):
    return jsonify({"error": "Text is required"}), 400

  speechRate = request.json.get("speechRate", configs["tts"]["speechRate"])
  try:
    speechRate = float(speechRate)
  except ValueError:
    speechRate = configs["tts"]["speechRate"]

  maxTextLength = configs["api"].get("maxTextLength", 2500)
  if (len(text) > maxTextLength):
    return jsonify({"error": f"Text exceeds maximum length of {maxTextLength} characters"}), 400

  if (VERBOSE):
    print(f"Creating a new job with text: {text[:50]}...")

  os.makedirs(STORE_PATH, exist_ok=True)
  currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  jobId = str(hashlib.md5(text.encode() + currentTime.encode()).hexdigest())
  jobDir = os.path.join(STORE_PATH, jobId)
  os.makedirs(jobDir, exist_ok=True)

  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER = QueueWatcher(current_app.config["ProcessJob"], maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ
    current_app.config["QUEUE_WATCHER"] = QUEUE_WATCHER
  JOB_HISTORY_OBJ.updateStatus(jobId, "queued")

  jobData = {
    "id"          : jobId,
    "status"      : "queued",
    "text"        : text,
    "speechRate"  : speechRate,
    "language"    : request.json.get("language", configs["tts"]["language"]),
    "voice"       : request.json.get("voice", configs["tts"]["voice"]),
    "videoQuality": request.json.get("videoQuality", None),
    "videoType"   : request.json.get("videoType", None),
    "createdAt"   : currentTime,
  }

  with open(os.path.join(jobDir, "job.json"), "w") as f:
    json.dump(jobData, f)

  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER.start()
  else:
    if (VERBOSE):
      print("Queue watcher is already running or not initialized.")

  return jsonify({"jobId": jobId}), 202


@apiBp.route("/api/v1/jobs/<jobId>", methods=["GET"])
def getJobStatus(jobId):
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  STORE_PATH = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]

  if (jobId not in JOB_HISTORY_OBJ.keys()):
    return jsonify({"error": "Job not found"}), 404

  status = JOB_HISTORY_OBJ.get(jobId, "unknown")
  jobDir = os.path.join(STORE_PATH, jobId)

  try:
    with open(os.path.join(jobDir, "job.json"), "r") as f:
      jobData = json.load(f)
  except FileNotFoundError:
    return jsonify({"error": "Job data not found"}), 404

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


@apiBp.route("/api/v1/jobs/triggerRemaining", methods=["POST"])
def triggerRemainingJobs():
  QUEUE_WATCHER = current_app.config["QUEUE_WATCHER"]
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  MAX_JOBS = current_app.config.get("MAX_JOBS", 1)
  MAX_TIMEOUT = current_app.config.get("MAX_TIMEOUT", 10)

  if (QUEUE_WATCHER and not QUEUE_WATCHER.is_alive()):
    QUEUE_WATCHER = QueueWatcher(current_app.config["ProcessJob"], maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ
    current_app.config["QUEUE_WATCHER"] = QUEUE_WATCHER
    QUEUE_WATCHER.start()
    return jsonify({"message": "Triggered processing for remaining queued jobs."}), 200
  elif (QUEUE_WATCHER and QUEUE_WATCHER.is_alive()):
    return jsonify({"message": "Queue watcher is already running."}), 200
  elif (not QUEUE_WATCHER):
    QUEUE_WATCHER = QueueWatcher(current_app.config["ProcessJob"], maxJobs=MAX_JOBS, maxTimeout=MAX_TIMEOUT)
    QUEUE_WATCHER.jobHistoryObj = JOB_HISTORY_OBJ
    current_app.config["QUEUE_WATCHER"] = QUEUE_WATCHER
    QUEUE_WATCHER.start()
    return jsonify({"message": "Initialized and started queue watcher."}), 200
  else:
    return jsonify({"message": "Queue watcher is already running or not initialized."}), 200


@apiBp.route("/api/v1/jobs/<jobId>/result", methods=["GET"])
def getProcessedVideo(jobId):
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  STORE_PATH = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]
  logger = current_app.config["logger"]

  if (jobId not in JOB_HISTORY_OBJ.keys()):
    logger.warning(f"Job {jobId} not found in the jobs.")
    return jsonify({"error": "Job not found"}), 404

  jobDir = os.path.join(STORE_PATH, jobId)
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

  if (jobData.get("status") != "completed"):
    logger.warning(f"Job {jobId} is not completed yet.")
    return jsonify({"error": "Job not completed yet"}), 400

  videoFormat = configs["ffmpeg"].get("videoFormat", "mp4")
  outputVideoPath = os.path.join(jobDir, f"{jobId}_Final.{videoFormat}")
  if (not os.path.exists(outputVideoPath)):
    logger.error(f"Processed video not found for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video not found"}), 404

  if (not os.access(outputVideoPath, os.R_OK)):
    logger.error(f"Processed video file is not readable for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video file is not accessible"}), 500

  if (os.path.getsize(outputVideoPath) == 0):
    logger.error(f"Processed video file is empty for job {jobId}: {outputVideoPath}")
    return jsonify({"error": "Processed video file is empty"}), 500

  logger.info(f"Returning processed video for job {jobId}: {outputVideoPath}")
  return send_file(outputVideoPath, as_attachment=True), 200


@apiBp.route("/api/v1/jobs/<jobId>", methods=["DELETE"])
def deleteProcessedVideo(jobId):
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  STORE_PATH = current_app.config["STORE_PATH"]

  if (jobId not in JOB_HISTORY_OBJ.keys()):
    return jsonify({"error": "Job not found"}), 404
  jobDir = os.path.join(STORE_PATH, jobId)

  if (os.path.exists(jobDir)):
    import shutil
    shutil.rmtree(jobDir)

  if (jobId in JOB_HISTORY_OBJ.keys()):
    JOB_HISTORY_OBJ.delete(jobId)

  return jsonify({"message": "Job data deleted successfully"}), 200


@apiBp.route("/api/v1/jobs/all", methods=["DELETE"])
def deleteAllProcessedVideos():
  '''Delete all processed videos and associated data for all jobs.'''
  STORE_PATH = current_app.config.get("STORE_PATH")
  JOB_HISTORY_OBJ = current_app.config.get("JOB_HISTORY_OBJ")

  # Remove all job directories and their contents.
  if (STORE_PATH and os.path.exists(STORE_PATH)):
    import shutil
    for item in os.listdir(STORE_PATH):
      itemPath = os.path.join(STORE_PATH, item)
      if (os.path.isdir(itemPath)):
        shutil.rmtree(itemPath)

  # Clear the job statuses dictionary.
  if (JOB_HISTORY_OBJ):
    JOB_HISTORY_OBJ.clear()

  # Return a success message.
  return jsonify({"message": "All job data deleted successfully"}), 200


@apiBp.route("/api/v1/audio-duration", methods=["POST"])
def getAudioDuration():
  # Get the file from the request.
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  allowedExtensions = current_app.config["configs"]["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  if (not any(file.filename.endswith(ext) for ext in allowedExtensions)):
    return jsonify({"error": f"File type not allowed, must be one of {allowedExtensions}"}), 400

  # Save the file to a temporary location.
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}"
  usedExtension = os.path.splitext(file.filename)[1]
  tempFilePath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempFilePath)

  # Calculate the audio duration using FFMPEG.
  try:
    duration = FFMPEGHelper().GetFileDuration(tempFilePath)
    # Round the duration to 2 decimal places.
    if (duration is not None):
      duration = round(duration, 2)
    else:
      duration = None
    # Delete the temporary file after processing.
    if (os.path.exists(tempFilePath)):
      os.remove(tempFilePath)
    if (duration is None):
      return jsonify({"error": "Could not determine audio duration"}), 500
    return jsonify({"duration": duration}), 200
  except Exception as e:
    current_app.logger.error(f"Error calculating audio duration: {str(e)}")
    return jsonify({"error": "Error calculating audio duration"}), 500


@apiBp.route("/api/v1/audio-size", methods=["POST"])
def getAudioSize():
  # Get the file from the request.
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  allowedExtensions = current_app.config["configs"]["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  if (not any(file.filename.endswith(ext) for ext in allowedExtensions)):
    return jsonify({"error": f"File type not allowed, must be one of {allowedExtensions}"}), 400

  # Save the file to a temporary location.
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}"
  usedExtension = os.path.splitext(file.filename)[1]
  tempFilePath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempFilePath)

  # Calculate the audio size.
  try:
    size = FFMPEGHelper().GetFileSize(tempFilePath)
    # If the size is None, it means the file could not be read.
    if (size is None):
      size = 0
    else:
      # Convert size to kilobytes (KB), Megabytes (MB), or Gigabytes (GB) as needed.
      if (size < 1024):
        size = f"{size} bytes"
      elif (size < 1024 * 1024):
        size = f"{size / 1024:.2f} KB"
      elif (size < 1024 * 1024 * 1024):
        size = f"{size / (1024 * 1024):.2f} MB"
      else:
        size = f"{size / (1024 * 1024 * 1024):.2f} GB"
    # Delete the temporary file after processing.
    if (os.path.exists(tempFilePath)):
      os.remove(tempFilePath)
    return jsonify({"size": size}), 200
  except Exception as e:
    current_app.logger.error(f"Error calculating audio size: {str(e)}")
    return jsonify({"error": "Error calculating audio size"}), 500


@apiBp.route("/api/v1/check-silence", methods=["POST"])
def checkAudioSilence():
  # Get the file from the request.
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  allowedExtensions = current_app.config["configs"]["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  if (not any(file.filename.endswith(ext) for ext in allowedExtensions)):
    return jsonify({"error": f"File type not allowed, must be one of {allowedExtensions}"}), 400

  # Save the file to a temporary location.
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}"
  usedExtension = os.path.splitext(file.filename)[1]
  tempFilePath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempFilePath)

  # Check for silence in the audio using FFMPEG.
  try:
    isSilent = FFMPEGHelper().IsFileSilent(tempFilePath)
    # Delete the temporary file after processing.
    if (os.path.exists(tempFilePath)):
      os.remove(tempFilePath)
    return jsonify({"isSilent": isSilent}), 200
  except Exception as e:
    current_app.logger.error(f"Error checking audio silence: {str(e)}")
    return jsonify({"error": "Error checking audio silence"}), 500


@apiBp.route("/api/v1/normalize-audio", methods=["POST"])
def normalizeAudio():
  # Get the file from the request.
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  allowedExtensions = current_app.config["configs"]["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  if (not any(file.filename.endswith(ext) for ext in allowedExtensions)):
    return jsonify({"error": f"File type not allowed, must be one of {allowedExtensions}"}), 400

  # Save the file to a temporary location.
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}"
  usedExtension = os.path.splitext(file.filename)[1]
  tempFilePath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempFilePath)

  # Normalize the audio using FFMPEG.
  try:
    outputPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_normalized{usedExtension}")
    if (os.path.exists(outputPath)):
      os.remove(outputPath)
    # Normalize the audio file using FFMPEG.
    isDone = asyncio.run(
      FFMPEGHelper().NormalizeAudio(tempFilePath, outputPath)
    )
    if (not isDone):
      current_app.logger.error("Failed to normalize audio.")
      return jsonify({"error": "Failed to normalize audio"}), 500
    # Check if the normalized audio file was created successfully.
    if (not os.path.exists(outputPath)):
      current_app.logger.error(f"Normalized audio file not found: {outputPath}")
      return jsonify({"error": "Normalized audio file not found"}), 404
    # Normalize the audio file path to ensure it is accessible.
    normalizedAudioPath = os.path.normpath(outputPath)
    if (not os.access(normalizedAudioPath, os.R_OK)):
      current_app.logger.error(f"Normalized audio file is not readable: {normalizedAudioPath}")
      return jsonify({"error": "Normalized audio file is not accessible"}), 500
    # If the file size is zero, return an error.
    if (os.path.getsize(normalizedAudioPath) == 0):
      current_app.logger.error(f"Normalized audio file is empty: {normalizedAudioPath}")
      return jsonify({"error": "Normalized audio file is empty"}), 500
    # Delete the temporary file after processing.
    if (os.path.exists(tempFilePath)):
      os.remove(tempFilePath)
    current_app.logger.info(f"Normalized audio file created successfully: {normalizedAudioPath}")
    # Return the normalized audio file as a link.
    return {
      "link"    : f"/api/v1/download/{uniqueFilename}_normalized{usedExtension}",
      "filename": f"{uniqueFilename}_normalized{usedExtension}"
    }
  except Exception as e:
    current_app.logger.error(f"Error normalizing audio: {str(e)}")
    return jsonify({"error": "Error normalizing audio"}), 500


@apiBp.route("/api/v1/download/<filename>", methods=["GET"])
def downloadFile(filename):
  STORE_PATH = current_app.config["STORE_PATH"]
  filePath = os.path.join(STORE_PATH, filename)

  if (not os.path.exists(filePath)):
    return jsonify({"error": "File not found"}), 404

  if (not os.access(filePath, os.R_OK)):
    return jsonify({"error": "File is not accessible"}), 403

  try:
    return send_file(filePath, as_attachment=True), 200
  except Exception as e:
    current_app.logger.error(f"Error sending file: {str(e)}")
    return jsonify({"error": "Error sending file"}), 500
