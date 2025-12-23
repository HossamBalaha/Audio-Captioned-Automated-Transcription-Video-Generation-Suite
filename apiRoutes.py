'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Permissions and Citation: Refer to the README file.
'''

import os, json, time, hashlib, asyncio, logging
from flask import Blueprint, jsonify, current_app, request, send_file
from WebHelpers import *
from TextToSpeechHelper import TextToSpeechHelper
from FFMPEGHelper import FFMPEGHelper

apiBp = Blueprint("api", __name__)

# Use module logger so messages go through Python's logging system and appear with Flask output.
logger = logging.getLogger(__name__)


@apiBp.route("/api/v1/status", methods=["GET"])
def GetServerStatus():
  return jsonify({"status": "Server is running"}), 200


@apiBp.route("/api/v1/ready", methods=["GET"])
def GetServerReady():
  JOB_HISTORY_OBJ = current_app.config["JOB_HISTORY_OBJ"]
  MAX_JOBS = current_app.config.get("MAX_JOBS", 1)
  noOfQuestedJobs = len([status for status in JOB_HISTORY_OBJ.values() if (status == "queued")])
  isBusy = (noOfQuestedJobs >= MAX_JOBS)
  if (not isBusy):
    return jsonify({"ready": True}), 200
  else:
    return jsonify({"ready": False, "jobsInProgress": len(JOB_HISTORY_OBJ)}), 503


@apiBp.route("/api/v1/languages", methods=["GET"])
def GetAvailableLanguages():
  languages = TextToSpeechHelper().GetAvailableLanguages()
  return jsonify({"languages": languages}), 200


@apiBp.route("/api/v1/videoTypes", methods=["GET"])
def GetAvailableVideoTypes():
  configs = current_app.config["configs"]
  videoTypes = configs["video"].get("availableTypes", ["Horizontal", "Vertical"])
  return jsonify({"videoTypes": videoTypes}), 200


@apiBp.route("/api/v1/videoQualities", methods=["GET"])
def GetAvailableVideoQualities():
  configs = current_app.config["configs"]
  videoQualities = configs["video"].get("availableQualities", [])
  return jsonify({"videoQualities": videoQualities}), 200


@apiBp.route("/api/v1/voices", methods=["GET"])
def GetAvailableVoices():
  typeKey = request.args.get("type", "list").lower()
  if (typeKey not in ["list", "dict"]):
    return jsonify({"error": "Invalid type parameter, must be 'list' or 'dict'"}), 400
  if (typeKey == "dict"):
    voices = TextToSpeechHelper().GetAvailableVoicesByLanguage()
  else:
    voices = TextToSpeechHelper().GetAvailableVoices()
  return jsonify({"voices": voices}), 200


@apiBp.route("/api/v1/jobs", methods=["GET"])
def GetAllJobs():
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
      except Exception:
        pass
  return jsonify({"jobs": jobsList}), 200


@apiBp.route("/api/v1/jobs", methods=["POST"])
def PostJob():
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
    logger.info(f"Creating a new job with text: {text[:50]}...")

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
      logger.info("Queue watcher is already running or not initialized.")

  return jsonify({"jobId": jobId}), 202


@apiBp.route("/api/v1/jobs/<jobId>", methods=["GET"])
def GetJobStatus(jobId):
  jobHistoryObj = current_app.config["JOB_HISTORY_OBJ"]
  storePath = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]

  if (jobId not in jobHistoryObj.keys()):
    return jsonify({"error": "Job not found"}), 404

  status = jobHistoryObj.get(jobId, "unknown")
  jobDir = os.path.join(storePath, jobId)

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
def TriggerRemainingJobs():
  queueWatcher = current_app.config["QUEUE_WATCHER"]
  jobHistoryObj = current_app.config["JOB_HISTORY_OBJ"]
  maxJobs = current_app.config.get("MAX_JOBS", 1)
  maxTimeout = current_app.config.get("MAX_TIMEOUT", 10)

  if (queueWatcher and not queueWatcher.is_alive()):
    queueWatcher = QueueWatcher(current_app.config["ProcessJob"], maxJobs=maxJobs, maxTimeout=maxTimeout)
    queueWatcher.jobHistoryObj = jobHistoryObj
    current_app.config["QUEUE_WATCHER"] = queueWatcher
    queueWatcher.start()
    return jsonify({"message": "Triggered processing for remaining queued jobs."}), 200
  elif (queueWatcher and queueWatcher.is_alive()):
    return jsonify({"message": "Queue watcher is already running."}), 200
  elif (not queueWatcher):
    queueWatcher = QueueWatcher(current_app.config["ProcessJob"], maxJobs=maxJobs, maxTimeout=maxTimeout)
    queueWatcher.jobHistoryObj = jobHistoryObj
    current_app.config["QUEUE_WATCHER"] = queueWatcher
    queueWatcher.start()
    return jsonify({"message": "Initialized and started queue watcher."}), 200
  else:
    return jsonify({"message": "Queue watcher is already running or not initialized."}), 200


@apiBp.route("/api/v1/jobs/<jobId>/result", methods=["GET"])
def GetProcessedVideo(jobId):
  jobHistoryObj = current_app.config["JOB_HISTORY_OBJ"]
  storePath = current_app.config["STORE_PATH"]
  configs = current_app.config["configs"]
  logger = current_app.config["logger"]

  if (jobId not in jobHistoryObj.keys()):
    logger.warning(f"Job {jobId} not found in the jobs.")
    return jsonify({"error": "Job not found"}), 404

  jobDir = os.path.join(storePath, jobId)
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
def DeleteProcessedVideo(jobId):
  jobHistoryObj = current_app.config["JOB_HISTORY_OBJ"]
  storePath = current_app.config["STORE_PATH"]

  if (jobId not in jobHistoryObj.keys()):
    return jsonify({"error": "Job not found"}), 404
  jobDir = os.path.join(storePath, jobId)

  if (os.path.exists(jobDir)):
    import shutil
    shutil.rmtree(jobDir)

  if (jobId in jobHistoryObj.keys()):
    jobHistoryObj.delete(jobId)

  return jsonify({"message": "Job data deleted successfully"}), 200


@apiBp.route("/api/v1/jobs/all", methods=["DELETE"])
def DeleteAllProcessedVideos():
  # Delete all processed videos and associated data for all jobs.
  storePath = current_app.config.get("STORE_PATH")
  jobHistoryObj = current_app.config.get("JOB_HISTORY_OBJ")

  # Remove all job directories and their contents.
  if (storePath and os.path.exists(storePath)):
    import shutil
    for item in os.listdir(storePath):
      itemPath = os.path.join(storePath, item)
      if (os.path.isdir(itemPath)):
        shutil.rmtree(itemPath)

  # Clear the job statuses dictionary.
  if (jobHistoryObj):
    jobHistoryObj.clear()

  # Return a success message.
  return jsonify({"message": "All job data deleted successfully"}), 200


@apiBp.route("/api/v1/audio-duration", methods=["POST"])
def GetAudioDuration():
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

  normalizeBitrate = request.form.get("normalizeBitrate", "256k")
  try:
    normalizeBitrate = str(normalizeBitrate)
    if (not normalizeBitrate.endswith("k")):
      normalizeBitrate += "k"
  except ValueError:
    normalizeBitrate = "256k"

  normalizeSampleRate = request.form.get("normalizeSampleRate", 44100)
  try:
    normalizeSampleRate = int(normalizeSampleRate)
    if (normalizeSampleRate <= 0):
      raise ValueError
  except ValueError:
    normalizeSampleRate = 44100

  normalizeFilter = request.form.get("normalizeFilter", "loudnorm")
  if (normalizeFilter not in ["loudnorm", "dynaudnorm", "acompressor", "volumedetect"]):
    normalizeFilter = "loudnorm"

  # Save the file to a temporary location.
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}"
  usedExtension = os.path.splitext(file.filename)[1]
  tempFilePath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempFilePath)

  if (usedExtension == ".mp3"):
    audioCodec = "libmp3lame"
    audioFormat = "mp3"
  elif (usedExtension == ".wav"):
    audioCodec = "pcm_s16le"
    audioFormat = "wav"
  elif (usedExtension == ".ogg"):
    audioCodec = "libvorbis"
    audioFormat = "ogg"
  else:
    audioCodec = "libmp3lame"
    audioFormat = "mp3"

  # Normalize the audio using FFMPEG.
  try:
    outputPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_normalized{usedExtension}")
    if (os.path.exists(outputPath)):
      os.remove(outputPath)
    logger.info(audioCodec, audioFormat, normalizeBitrate, normalizeSampleRate, normalizeFilter)
    # Normalize the audio file using FFMPEG.
    isDone = asyncio.run(
      FFMPEGHelper().NormalizeAudio(
        tempFilePath,
        outputPath,
        audioCodec=audioCodec,
        audioFormat=audioFormat,
        audioBitrate=normalizeBitrate,
        sampleRate=normalizeSampleRate,
        normalizationFilter=normalizeFilter,
      )
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


@apiBp.route("/api/v1/generate-silent-audio", methods=["POST"])
def generateSilentAudio():
  data = request.get_json()
  if (not data):
    return jsonify({"error": "Invalid JSON data"}), 400
  duration = data.get("silentDuration", 1)
  try:
    duration = float(duration)
    if (duration <= 0):
      raise ValueError
  except ValueError:
    return jsonify({"error": "Duration must be a positive number"}), 400

  configs = current_app.config["configs"]
  STORE_PATH = current_app.config["STORE_PATH"]
  allowedExtensions = configs["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  outputFormat = data.get("silentFormat", ".wav").lower()
  if (outputFormat not in allowedExtensions):
    outputFormat = ".wav"

  uniqueFilename = f"silent_{int(duration)}s_{hashlib.md5(str(time.time()).encode()).hexdigest()}"
  outputPath = os.path.join(STORE_PATH, f"{uniqueFilename}{outputFormat}")

  try:
    if (outputFormat == ".mp3"):
      audioCodec = "libmp3lame"
      audioFormat = "mp3"
    elif (outputFormat == ".wav"):
      audioCodec = "pcm_s16le"
      audioFormat = "wav"
    elif (outputFormat == ".ogg"):
      audioCodec = "libvorbis"
      audioFormat = "ogg"
    else:
      audioCodec = "libmp3lame"
      audioFormat = "mp3"

    isDone = asyncio.run(
      FFMPEGHelper().GenerateSilentAudio(outputPath, duration, audioCodec=audioCodec, audioFormat=audioFormat)
    )
    if (not isDone):
      return jsonify({"error": "Failed to generate silent audio"}), 500
    if (not os.path.exists(outputPath)):
      return jsonify({"error": "Silent audio file not found"}), 404
    if (not os.access(outputPath, os.R_OK)):
      return jsonify({"error": "Silent audio file is not accessible"}), 500
    if (os.path.getsize(outputPath) == 0):
      return jsonify({"error": "Silent audio file is empty"}), 500
    return {
      "link"    : f"/api/v1/download/{uniqueFilename}{outputFormat}",
      "filename": f"{uniqueFilename}{outputFormat}"
    }
  except Exception as e:
    current_app.logger.error(f"Error generating silent audio: {str(e)}")
    return jsonify({"error": "Error generating silent audio"}), 500


@apiBp.route("/api/v1/convert-audio", methods=["POST"])
def convertAudio():
  # Convert audio: format, bitrate, sample rate, channels, optional trim
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  configs = current_app.config["configs"]
  allowedExtensions = configs["audio"].get("allowedExtensions", [".mp3", ".wav", ".ogg"])
  usedExtension = os.path.splitext(file.filename)[1].lower()
  if (usedExtension not in allowedExtensions):
    return jsonify({"error": f"File type not allowed, must be one of {allowedExtensions}"}), 400

  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)

  # Parameters
  outFormat = request.form.get("outputFormat", usedExtension.replace('.', ''))
  if (not outFormat.startswith(".")):
    outFormat = "." + outFormat
  if (outFormat not in allowedExtensions):
    outFormat = usedExtension

  bitrate = request.form.get("bitrate", None)
  try:
    sampleRate = int(request.form.get("sampleRate", configs["ffmpeg"].get("sampleRate", 44100)))
  except Exception:
    sampleRate = configs["ffmpeg"].get("sampleRate", 44100)
  try:
    channels = int(request.form.get("channels", configs["ffmpeg"].get("channels", 2)))
  except Exception:
    channels = configs["ffmpeg"].get("channels", 2)

  startTime = request.form.get("startTime", None)
  endTime = request.form.get("endTime", None)

  # If trimming requested, create a trimmed temp file first
  workingPath = tempPath
  try:
    if (startTime is not None and endTime is not None and startTime != "" and endTime != ""):
      try:
        s = float(startTime)
        e = float(endTime)
        trimmedPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_trimmed{usedExtension}")
        isDone = asyncio.run(FFMPEGHelper().TrimAudio(workingPath, trimmedPath, s, e))
        if (not isDone):
          raise Exception("Failed to trim file")
        # remove original temp and use trimmed
        if (os.path.exists(workingPath)):
          os.remove(workingPath)
        workingPath = trimmedPath
      except Exception as ex:
        current_app.logger.error(f"Error trimming audio: {str(ex)}")
        if (os.path.exists(tempPath)):
          os.remove(tempPath)
        return jsonify({"error": "Failed to trim audio"}), 500

    # Build output path
    outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_converted{outFormat}")
    # Use NormalizeAudio function as a general re-encoder (it applies codec/bitrate/sample rate)
    # Choose codec based on extension
    if (outFormat == ".mp3"):
      audioCodec = "libmp3lame"
      audioFormat = "mp3"
    elif (outFormat == ".wav"):
      audioCodec = "pcm_s16le"
      audioFormat = "wav"
    elif (outFormat == ".ogg"):
      audioCodec = "libvorbis"
      audioFormat = "ogg"
    else:
      audioCodec = configs["ffmpeg"].get("audioCodec", "libmp3lame")
      audioFormat = outFormat.replace('.', '')

    # Set bitrate if provided
    if (bitrate and not bitrate.endswith('k')):
      bitrate = str(bitrate) + 'k'

    isDone = asyncio.run(
      FFMPEGHelper().NormalizeAudio(
        workingPath,
        outPath,
        audioCodec=audioCodec,
        audioFormat=audioFormat,
        audioBitrate=bitrate or configs["ffmpeg"].get("audioBitrate", "256k"),
        sampleRate=sampleRate,
        channels=channels,
        normalizationFilter=request.form.get("normalizeFilter",
                                             configs["ffmpeg"].get("normalizationFilter", "loudnorm"))
      )
    )

    if (os.path.exists(workingPath)):
      try:
        os.remove(workingPath)
      except Exception:
        pass

    if (not isDone or not os.path.exists(outPath)):
      current_app.logger.error("Conversion failed or output missing")
      return jsonify({"error": "Failed to convert audio"}), 500

    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error converting audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error converting audio"}), 500


@apiBp.route("/api/v1/change-volume", methods=["POST"])
def changeVolume():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    volume = float(request.form.get("volume", 1.0))
  except Exception:
    volume = 1.0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_vol{usedExtension}")
  try:
    ff = FFMPEGHelper()
    cmd = [
      "ffmpeg", "-i", tempPath,
      "-af", f"volume={volume}",
      "-y", outPath
    ]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "ChangeVolume"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to change volume"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error changing volume: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error changing volume"}), 500


@apiBp.route("/api/v1/change-speed", methods=["POST"])
def changeSpeed():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    speed = float(request.form.get("speed", 1.0))
  except Exception:
    speed = 1.0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_spd{usedExtension}")
  try:
    # atempo supports 0.5-2.0 per instance; chain if needed
    tempo = speed
    if (tempo <= 0):
      raise ValueError
    atempoFilters = []
    while (tempo > 2.0):
      atempoFilters.append("atempo=2.0")
      tempo /= 2.0
    while (tempo < 0.5):
      atempoFilters.append("atempo=0.5")
      tempo /= 0.5
    atempoFilters.append(f"atempo={tempo}")
    af = ",".join(atempoFilters)
    ff = FFMPEGHelper()
    cmd = ["ffmpeg", "-i", tempPath, "-af", af, "-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "ChangeSpeed"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to change speed"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error changing speed: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error changing speed"}), 500


@apiBp.route("/api/v1/reverse-audio", methods=["POST"])
def reverseAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_rev{usedExtension}")
  try:
    ff = FFMPEGHelper()
    cmd = ["ffmpeg", "-i", tempPath, "-af", "areverse", "-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "ReverseAudio"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to reverse audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error reversing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error reversing audio"}), 500


@apiBp.route("/api/v1/extract-audio", methods=["POST"])
def extractAudio():
  if (not request.files or "videoFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["videoFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  usedExtension = ".mp3"
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{os.path.splitext(file.filename)[1]}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_extracted{usedExtension}")
  try:
    ff = FFMPEGHelper()
    # Check whether the uploaded video actually contains an audio stream.
    try:
      hasAudio = ff.HasAudioStream(tempPath)
    except Exception as e:
      hasAudio = False
    if (not hasAudio):
      # Clean up temp file and return a 400 (bad request) indicating no audio present.
      try:
        if (os.path.exists(tempPath)):
          os.remove(tempPath)
      except Exception:
        pass
      return jsonify({"error": "Uploaded video contains no audio stream"}), 400

    # Extract audio and convert to mp3
    cmd = ["ffmpeg", "-i", tempPath, "-vn", "-acodec", "libmp3lame", "-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "ExtractAudio"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to extract audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error extracting audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error extracting audio"}), 500


@apiBp.route("/api/v1/concat-audio", methods=["POST"])
def concatAudio():
  if (not request.files or "audioFiles" not in request.files):
    return jsonify({"error": "No files provided"}), 400
  files = request.files.getlist("audioFiles")
  if (len(files) == 0):
    return jsonify({"error": "No files selected"}), 400
  storedPaths = []
  try:
    for f in files:
      ext = os.path.splitext(f.filename)[1]
      unique = f"{hashlib.md5(f.filename.encode()).hexdigest()}_{int(time.time())}"
      p = os.path.join(current_app.config["STORE_PATH"], f"{unique}{ext}")
      f.save(p)
      storedPaths.append(p)
    outPath = os.path.join(current_app.config["STORE_PATH"], f"concat_{int(time.time())}.mp3")
    isDone = asyncio.run(FFMPEGHelper().ConcatAudioFiles(storedPaths, outPath))
    # cleanup inputs
    for p in storedPaths:
      try:
        os.remove(p)
      except Exception:
        pass
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to concatenate audio files"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error concatenating audio: {str(e)}")
    for p in storedPaths:
      try:
        os.remove(p)
      except Exception:
        pass
    return jsonify({"error": "Error concatenating audio"}), 500


@apiBp.route("/api/v1/split-audio", methods=["POST"])
def splitAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    segmentDuration = float(request.form.get("segmentDuration", 10))
  except Exception:
    segmentDuration = 10.0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  try:
    totalDur = FFMPEGHelper().GetFileDuration(tempPath)
    if (totalDur is None):
      raise Exception("Could not determine duration")
    parts = []
    start = 0.0
    idx = 0
    while start < totalDur:
      end = min(start + segmentDuration, totalDur)
      outPart = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_part{idx}{usedExtension}")
      isDone = asyncio.run(FFMPEGHelper().TrimAudio(tempPath, outPart, start, end))
      if (not isDone or not os.path.exists(outPart)):
        raise Exception("Failed to create segment")
      parts.append(outPart)
      start = end
      idx += 1
    # Create a zip archive of parts
    import zipfile
    zipName = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_parts.zip")
    with zipfile.ZipFile(zipName, 'w') as zf:
      for p in parts:
        zf.write(p, arcname=os.path.basename(p))
    # cleanup parts and original
    for p in parts:
      try:
        os.remove(p)
      except Exception:
        pass
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    return {"link": f"/api/v1/download/{os.path.basename(zipName)}", "filename": os.path.basename(zipName)}
  except Exception as e:
    current_app.logger.error(f"Error splitting audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error splitting audio"}), 500


@apiBp.route("/api/v1/fade-audio", methods=["POST"])
def fadeAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    fadeIn = float(request.form.get("fadeIn", 0))
  except Exception:
    fadeIn = 0
  try:
    fadeOut = float(request.form.get("fadeOut", 0))
  except Exception:
    fadeOut = 0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_fade{usedExtension}")
  try:
    afParts = []
    if (fadeIn > 0):
      afParts.append(f"afade=t=in:st=0:d={fadeIn}")
    if (fadeOut > 0):
      # Need file duration to place fade out start
      duration = FFMPEGHelper().GetFileDuration(tempPath) or 0
      startOut = max(0, duration - fadeOut)
      afParts.append(f"afade=t=out:st={startOut}:d={fadeOut}")
    af = ",".join(afParts) if afParts else ""
    ff = FFMPEGHelper()
    cmd = ["ffmpeg", "-i", tempPath]
    if af:
      cmd += ["-af", af]
    cmd += ["-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "FadeAudio"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to add fade"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error applying fade: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error applying fade"}), 500


@apiBp.route("/api/v1/remove-vocals", methods=["POST"])
def removeVocals():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_novocals{usedExtension}")
  try:
    # Basic center-channel vocal removal for stereo files
    ff = FFMPEGHelper()
    cmd = ["ffmpeg", "-i", tempPath, "-af", "pan=stereo|c0=c0-c1|c1=c1-c0", "-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "RemoveVocals"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to remove vocals"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error removing vocals: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error removing vocals"}), 500


@apiBp.route("/api/v1/equalize-audio", methods=["POST"])
def equalizeAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    freq = float(request.form.get("freq", 1000))
  except Exception:
    freq = 1000.0
  try:
    width = float(request.form.get("width", 2))
  except Exception:
    width = 2.0
  try:
    gain = float(request.form.get("gain", 5))
  except Exception:
    gain = 5.0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_eq{usedExtension}")
  try:
    # Use equalizer filter: equalizer=f=<freq>:width_type=h:width=<width>:g=<gain>
    filterStr = f"equalizer=f={freq}:width_type=h:width={width}:g={gain}"
    ff = FFMPEGHelper()
    cmd = ["ffmpeg", "-i", tempPath, "-af", filterStr, "-y", outPath]
    success, proc = asyncio.run(ff._ExecuteFFmpegCommand(cmd, "EqualizeAudio"))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not success or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to apply equalizer"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error equalizing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error equalizing audio"}), 500


@apiBp.route("/api/v1/mix-audio", methods=["POST"])
def mixAudio():
  if (not request.files or "audioFiles" not in request.files):
    return jsonify({"error": "No files provided"}), 400
  files = request.files.getlist("audioFiles")
  if (len(files) < 2):
    return jsonify({"error": "At least 2 audio files required"}), 400
  storedPaths = []
  try:
    for f in files:
      ext = os.path.splitext(f.filename)[1]
      unique = f"{hashlib.md5(f.filename.encode()).hexdigest()}_{int(time.time())}"
      p = os.path.join(current_app.config["STORE_PATH"], f"{unique}{ext}")
      f.save(p)
      storedPaths.append(p)
    # Get volume levels from form data (comma-separated).
    volumesStr = request.form.get("volumes", "")
    volumes = None
    if (volumesStr):
      try:
        volumes = [float(v.strip()) for v in volumesStr.split(",")]
      except Exception:
        volumes = None
    duration = request.form.get("duration", "longest")
    outPath = os.path.join(current_app.config["STORE_PATH"], f"mixed_{int(time.time())}.mp3")
    isDone = asyncio.run(FFMPEGHelper().MixAudioFiles(storedPaths, outPath, volumes=volumes, duration=duration))
    for p in storedPaths:
      try:
        os.remove(p)
      except Exception:
        pass
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to mix audio files"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error mixing audio: {str(e)}")
    for p in storedPaths:
      try:
        os.remove(p)
      except Exception:
        pass
    return jsonify({"error": "Error mixing audio"}), 500


@apiBp.route("/api/v1/reduce-noise", methods=["POST"])
def reduceNoise():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    noiseReduction = int(request.form.get("noiseReduction", 20))
  except Exception:
    noiseReduction = 20
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_noisereduced{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().ReduceNoise(tempPath, outPath, noiseReduction=noiseReduction))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to reduce noise"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error reducing noise: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error reducing noise"}), 500


@apiBp.route("/api/v1/remove-silence", methods=["POST"])
def removeSilence():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    threshold = int(request.form.get("threshold", -50))
    duration = float(request.form.get("duration", 0.5))
  except Exception:
    threshold = -50
    duration = 0.5
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_nosilence{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().RemoveSilence(tempPath, outPath, threshold=threshold, duration=duration))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to remove silence"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error removing silence: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error removing silence"}), 500


@apiBp.route("/api/v1/enhance-audio", methods=["POST"])
def enhanceAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    bassGain = int(request.form.get("bassGain", 0))
    trebleGain = int(request.form.get("trebleGain", 0))
  except Exception:
    bassGain = 0
    trebleGain = 0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_enhanced{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().EnhanceAudio(tempPath, outPath, bassGain=bassGain, trebleGain=trebleGain))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to enhance audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error enhancing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error enhancing audio"}), 500


@apiBp.route("/api/v1/compress-audio", methods=["POST"])
def compressAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    threshold = int(request.form.get("threshold", -20))
    ratio = int(request.form.get("ratio", 4))
    attack = int(request.form.get("attack", 200))
    release = int(request.form.get("release", 1000))
    makeupGain = int(request.form.get("makeupGain", 0))
  except Exception:
    threshold = -20
    ratio = 4
    attack = 200
    release = 1000
    makeupGain = 0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_compressed{usedExtension}")
  try:
    isDone = asyncio.run(
      FFMPEGHelper().CompressAudio(tempPath, outPath, threshold=threshold, ratio=ratio, attack=attack,
                                   release=release, makeupGain=makeupGain))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to compress audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error compressing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error compressing audio"}), 500


@apiBp.route("/api/v1/convert-channels", methods=["POST"])
def convertChannels():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    targetChannels = int(request.form.get("targetChannels", 1))
  except Exception:
    targetChannels = 1
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  channelName = "mono" if targetChannels == 1 else "stereo"
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_{channelName}{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().ConvertChannels(tempPath, outPath, targetChannels=targetChannels))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to convert channels"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error converting channels: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error converting channels"}), 500


@apiBp.route("/api/v1/loop-audio", methods=["POST"])
def loopAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    loopCount = int(request.form.get("loopCount", 2))
    totalDuration = request.form.get("totalDuration", None)
    if (totalDuration):
      totalDuration = float(totalDuration)
  except Exception:
    loopCount = 2
    totalDuration = None
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_looped{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().LoopAudio(tempPath, outPath, loopCount=loopCount, totalDuration=totalDuration))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to loop audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error looping audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error looping audio"}), 500


@apiBp.route("/api/v1/shift-pitch", methods=["POST"])
def shiftPitch():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    semitones = int(request.form.get("semitones", 0))
  except Exception:
    semitones = 0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_pitched{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().ShiftPitch(tempPath, outPath, semitones=semitones))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to shift pitch"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error shifting pitch: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error shifting pitch"}), 500


@apiBp.route("/api/v1/add-echo", methods=["POST"])
def addEcho():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    delay = int(request.form.get("delay", 1000))
    decay = float(request.form.get("decay", 0.5))
  except Exception:
    delay = 1000
    decay = 0.5
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_echo{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().AddEcho(tempPath, outPath, delay=delay, decay=decay))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to add echo"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error adding echo: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error adding echo"}), 500


@apiBp.route("/api/v1/adjust-stereo", methods=["POST"])
def adjustStereo():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    width = float(request.form.get("width", 1.0))
  except Exception:
    width = 1.0
  usedExtension = os.path.splitext(file.filename)[1]
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{usedExtension}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_stereo{usedExtension}")
  try:
    isDone = asyncio.run(FFMPEGHelper().AdjustStereoWidth(tempPath, outPath, width=width))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to adjust stereo"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error adjusting stereo: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error adjusting stereo"}), 500


@apiBp.route("/api/v1/generate-waveform", methods=["POST"])
def generateWaveform():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 240))
    colors = request.form.get("colors", "blue")
  except Exception:
    width = 1280
    height = 240
    colors = "blue"
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{os.path.splitext(file.filename)[1]}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_waveform.png")
  try:
    isDone = asyncio.run(FFMPEGHelper().GenerateWaveform(tempPath, outPath, width=width, height=height, colors=colors))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to generate waveform"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error generating waveform: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error generating waveform"}), 500


@apiBp.route("/api/v1/generate-spectrum", methods=["POST"])
def generateSpectrum():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 720))
    colorScheme = request.form.get("colorScheme", "rainbow")
  except Exception:
    width = 1280
    height = 720
    colorScheme = "rainbow"
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{os.path.splitext(file.filename)[1]}")
  file.save(tempPath)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}_spectrum.mp4")
  try:
    isDone = asyncio.run(
      FFMPEGHelper().GenerateSpectrum(tempPath, outPath, width=width, height=height, colorScheme=colorScheme))
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to generate spectrum"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error generating spectrum: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error generating spectrum"}), 500


@apiBp.route("/api/v1/crossfade-audio", methods=["POST"])
def crossfadeAudio():
  if (not request.files or "firstAudio" not in request.files or "secondAudio" not in request.files):
    return jsonify({"error": "Two audio files required"}), 400
  file1 = request.files["firstAudio"]
  file2 = request.files["secondAudio"]
  if (file1.filename == "" or file2.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  try:
    duration = int(request.form.get("duration", 3))
  except Exception:
    duration = 3
  unique1 = f"{hashlib.md5(file1.filename.encode()).hexdigest()}_{int(time.time())}"
  unique2 = f"{hashlib.md5(file2.filename.encode()).hexdigest()}_{int(time.time()) + 1}"
  path1 = os.path.join(current_app.config["STORE_PATH"], f"{unique1}{os.path.splitext(file1.filename)[1]}")
  path2 = os.path.join(current_app.config["STORE_PATH"], f"{unique2}{os.path.splitext(file2.filename)[1]}")
  file1.save(path1)
  file2.save(path2)
  outPath = os.path.join(current_app.config["STORE_PATH"], f"crossfade_{int(time.time())}.mp3")
  try:
    isDone = asyncio.run(FFMPEGHelper().CrossfadeAudio(path1, path2, outPath, duration=duration))
    if (os.path.exists(path1)):
      os.remove(path1)
    if (os.path.exists(path2)):
      os.remove(path2)
    if (not isDone or not os.path.exists(outPath)):
      return jsonify({"error": "Failed to crossfade audio"}), 500
    return {"link": f"/api/v1/download/{os.path.basename(outPath)}", "filename": os.path.basename(outPath)}
  except Exception as e:
    current_app.logger.error(f"Error crossfading audio: {str(e)}")
    for p in [path1, path2]:
      try:
        if (os.path.exists(p)):
          os.remove(p)
      except Exception:
        pass
    return jsonify({"error": "Error crossfading audio"}), 500


@apiBp.route("/api/v1/analyze-audio", methods=["POST"])
def analyzeAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{os.path.splitext(file.filename)[1]}")
  file.save(tempPath)
  try:
    analysis = FFMPEGHelper().AnalyzeAudio(tempPath)
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (analysis is None):
      return jsonify({"error": "Failed to analyze audio"}), 500
    return jsonify(analysis), 200
  except Exception as e:
    current_app.logger.error(f"Error analyzing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error analyzing audio"}), 500


@apiBp.route("/api/v1/transcribe-audio", methods=["POST"])
def transcribeAudio():
  if (not request.files or "audioFile" not in request.files):
    return jsonify({"error": "No file provided"}), 400
  file = request.files["audioFile"]
  if (file.filename == ""):
    return jsonify({"error": "No file selected"}), 400
  language = request.form.get("language", "en")
  outputFormat = request.form.get("outputFormat", "txt")
  uniqueFilename = f"{hashlib.md5(file.filename.encode()).hexdigest()}_{int(time.time())}"
  tempPath = os.path.join(current_app.config["STORE_PATH"], f"{uniqueFilename}{os.path.splitext(file.filename)[1]}")
  file.save(tempPath)
  try:
    from WhisperTranscribeHelper import WhisperTranscribeHelper
    transcriber = WhisperTranscribeHelper()
    result = transcriber.Transcribe(tempPath, language=language)
    if (os.path.exists(tempPath)):
      os.remove(tempPath)
    if (result is None):
      return jsonify({"error": "Failed to transcribe audio"}), 500
    # Format output based on request.
    if (outputFormat == "json"):
      return jsonify(result), 200
    elif (outputFormat == "txt"):
      text = result.get("text", "")
      return jsonify({"transcription": text}), 200
    elif (outputFormat == "srt"):
      # Generate SRT format from segments.
      srtContent = ""
      if ("segments" in result):
        for i, seg in enumerate(result["segments"]):
          srtContent += f"{i + 1}\n"
          start = seg.get("start", 0)
          end = seg.get("end", 0)
          srtContent += f"{formatSRTTime(start)} --> {formatSRTTime(end)}\n"
          srtContent += f"{seg.get('text', '').strip()}\n\n"
      return jsonify({"srt": srtContent}), 200
    else:
      return jsonify(result), 200
  except Exception as e:
    current_app.logger.error(f"Error transcribing audio: {str(e)}")
    if (os.path.exists(tempPath)):
      try:
        os.remove(tempPath)
      except Exception:
        pass
    return jsonify({"error": "Error transcribing audio."}), 500


def formatSRTTime(seconds):
  hours = int(seconds // 3600)
  minutes = int((seconds % 3600) // 60)
  secs = int(seconds % 60)
  millis = int((seconds % 1) * 1000)
  return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


@apiBp.route("/api/v1/download/<filename>", methods=["GET"])
def downloadFile(filename):
  STORE_PATH = current_app.config["STORE_PATH"]
  # Sanitize filename to prevent path traversal
  safeFilename = os.path.basename(filename)
  filePath = os.path.join(STORE_PATH, safeFilename)

  if (not os.path.exists(filePath)):
    return jsonify({"error": "File not found"}), 404

  if (not os.access(filePath, os.R_OK)):
    return jsonify({"error": "File is not accessible"}), 403

  # Optionally restrict allowed file types:
  # allowedExtensions = [".mp3", ".wav", ".ogg", ".mp4", ".json"]
  # if not any(filePath.endswith(ext) for ext in allowedExtensions):
  #     return jsonify({"error": "File type not allowed"}), 403

  try:
    return send_file(filePath, as_attachment=True), 200
  except Exception as e:
    current_app.logger.error(f"Error sending file: {str(e)}")
    return jsonify({"error": "Error sending file"}), 500
