'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Permissions and Citation: Refer to the README file.
'''

import ffmpeg, subprocess, tempfile, yaml, os, random, asyncio, re, logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from TextHelper import EscapeText

# Use module logger so messages go through Python's logging system and appear with Flask output.
logger = logging.getLogger(__name__)

with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)

# Get the verbose setting from the config.
VERBOSE = configs.get("verbose", False)


class FFMPEGHelper(object):
  r'''
  A helper class for FFMPEG operations.
  This class provides methods to perform various video and audio processing tasks using FFMPEG.
  '''

  def DetectFFmpegPath(self):
    r'''Detect ffmpeg executable path on Windows or PATH.'''
    candidates = []
    # Check PATH.
    for p in os.environ.get("PATH", "").split(os.pathsep):
      exe = os.path.join(p, "ffmpeg.exe")
      if os.path.isfile(exe):
        candidates.append(exe)
    # Common install locations.
    common = [
      r"C:\\ffmpeg\\bin\\ffmpeg.exe",
      r"C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
      r"C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
    ]
    for exe in common:
      if os.path.isfile(exe):
        candidates.append(exe)
    return candidates[0] if candidates else None

  def GetFileDuration(self, filePath):
    r'''
    Get the duration of a file in seconds.
    This function uses ffmpeg to retrieve the duration of a file.

    Parameters:
      filePath (str): Path to the input file.

    Returns:
      float: Duration of the file in seconds.
    '''

    try:
      probe = ffmpeg.probe(filePath)
      duration = float(probe["format"]["duration"])
      return duration
    except ffmpeg.Error as e:
      if (VERBOSE):
        logger.info("Function `GetFileDuration` encountered an error:")
        logger.info(f"Error getting file duration: {e.stderr}")
      return None

  def GetFilesDuration(self, filePaths):
    r'''
    Get the total duration of multiple files in seconds.
    This function retrieves the duration of each file and sums them up.

    Parameters:
      filePaths (list): List of paths to input files.

    Returns:
      float: Total duration of all files in seconds.
    '''

    totalDuration = 0.0
    for filePath in filePaths:
      duration = self.GetFileDuration(filePath)
      if (duration is not None):
        totalDuration += duration
      else:
        if (VERBOSE):
          logger.info(f"Could not get duration for file: {filePath}")
          return None
    return totalDuration

  def GetFileSize(self, filePath):
    r'''
    Get the size of a file in bytes.
    This function retrieves the size of a file.

    Parameters:
      filePath (str): Path to the input file.

    Returns:
      int: Size of the file in bytes.
    '''

    try:
      return os.path.getsize(filePath)
    except Exception as e:
      if (VERBOSE):
        logger.info("Function `GetFileSize` encountered an error:")
        logger.info(f"Error getting file size: {str(e)}")
      return None

  def GetFileDimensions(self, filePath):
    r'''
    Get the dimensions of a video file.
    This function uses ffmpeg to retrieve the width and height of a video file.

    Parameters:
      filePath (str): Path to the input video file.

    Returns:
      tuple: (width, height) of the video file, or None if an error occurs.
    '''

    try:
      probe = ffmpeg.probe(filePath)
      videoStream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
      if videoStream is not None:
        width = int(videoStream["width"])
        height = int(videoStream["height"])
        return (width, height)
      else:
        if (VERBOSE):
          logger.info("No video stream found in the file.")
        return None
    except ffmpeg.Error as e:
      if (VERBOSE):
        logger.info("Function `GetFileDimensions` encountered an error:")
        logger.info(f"Error getting video dimensions: {e.stderr}")
      return None

  def IsFileSilent(self, filePath):
    r'''
    Check if a video file is silent based on its audio content.
    This function uses ffmpeg to analyze the audio stream of a video file.

    Parameters:
      filePath (str): Path to the input file.

    Returns:
      bool: True if the video is silent, False otherwise.
    '''

    try:
      # First check if the file exists and has audio streams.
      probe = ffmpeg.probe(filePath)
      audioStream = None
      if ("streams" in probe and len(probe["streams"]) > 0):
        # Look for audio streams specifically.
        for stream in probe["streams"]:
          if (stream.get("codec_type") == "audio"):
            audioStream = stream
            break

      if (audioStream is None):
        if (VERBOSE):
          logger.info("No audio stream found in the video file.")
        return True  # No audio = silent.

      # Use ffmpeg to get the average volume of the audio stream.
      out, err = (
        ffmpeg
        .input(filePath)
        .filter("volumedetect")
        .output("pipe:", format="null")
        .run(capture_stdout=True, capture_stderr=True)
      )

      # Parse the stderr output to find the mean volume (volumedetect outputs to stderr).
      meanVolume = None
      stderrOutput = err.decode() if (err) else ""

      for line in stderrOutput.splitlines():
        if ("mean_volume" in line):
          # Extract the dB value from a line like "mean_volume: -91.0 dB".
          meanVolume = float(line.split("mean_volume:")[1].strip().replace("dB", "").strip())
          break

      if (meanVolume is not None):
        if (VERBOSE):
          logger.info(f"Mean Volume: {meanVolume} dB")
        # Convert dB to a linear scale for comparison.
        meanVolume = 10 ** (meanVolume / 20)  # Convert dB to linear scale.
        if (VERBOSE):
          logger.info(f"Mean Volume (linear scale): {meanVolume}")
        # Check if the mean volume is below the threshold.
        isSilent = (meanVolume < configs["ffmpeg"]["isSilentThreshold"])
        return isSilent
      else:
        if (VERBOSE):
          logger.info("Could not determine the mean volume from the audio stream.")
        return False
    except ffmpeg.Error as e:
      if (VERBOSE):
        logger.info("Function `IsFileSilent` encountered an error:")
        logger.info(f"Error checking if video is silent: {e.stderr}")
      return False

  def HasAudioStream(self, filePath):
    r'''
    Check if a video file has an audio stream.
    This function uses ffmpeg to analyze the streams of a video file.

    Parameters:
      filePath (str): Path to the input file.

    Returns:
      bool: True if the video has an audio stream, False otherwise.
    '''

    try:
      probe = ffmpeg.probe(filePath)
      for stream in probe["streams"]:
        if (stream.get("codec_type") == "audio"):
          return True
      return False
    except ffmpeg.Error as e:
      if (VERBOSE):
        logger.info("Function `HasAudioStream` encountered an error:")
        logger.info(f"Error checking audio stream: {e.stderr}")
      return False

  async def _ExecuteFFmpegCommand(self, command, functionName="", logPath=None):
    r'''
    Execute an FFMPEG command asynchronously.
    This method runs the provided FFMPEG command and returns the result.

    Parameters:
      command (list): List of command arguments for FFMPEG.
      functionName (str): Name of the function calling this method (for logging).
      logPath (str): Optional path to write ffmpeg stdout/stderr for debugging.

   Returns:
      bool: True if the command was successful, False otherwise.
      process: The subprocess object containing the result of the command.      
    '''

    try:
      if (VERBOSE):
        logger.info(f"Executing command for `{functionName}`:\n{command}")
      process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
      )
      stdout, stderr = await process.communicate()
      stdoutDecoded = (stdout.decode() if stdout else "")
      stderrDecoded = (stderr.decode() if stderr else "")

      # If a logPath is provided, persist stdout/stderr to that file for debugging and UI exposure.
      try:
        if logPath:
          with open(logPath, "w", encoding="utf-8", errors="ignore") as lf:
            lf.write(f"COMMAND: {' '.join(command)}\n\n")
            lf.write("=== STDOUT ===\n")
            lf.write(stdoutDecoded or "(no stdout)\n")
            lf.write("\n=== STDERR ===\n")
            lf.write(stderrDecoded or "(no stderr)\n")
      except Exception:
        # Non-fatal if logging fails.
        pass

      if (process.returncode != 0):
        if (VERBOSE):
          logger.info(f"Function `{functionName}` encountered an error:")
          logger.info(f"Error executing command: {stderrDecoded}")
        return False, process
      else:
        if (VERBOSE):
          logger.info(f"Command `{functionName}` executed successfully.")
        return True, process
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Function `{functionName}` encountered an error:")
        logger.info(f"Error executing command: {str(e)}")
      return False, None

  async def NormalizeAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the normalized audio file.
    audioCodec=None,  # Audio codec to use (optional).
    audioFormat=None,  # Audio format to use (optional).
    audioBitrate=None,  # Audio bitrate to use (optional).
    normalizationFilter=None,  # Normalization filter to use (optional).
    sampleRate=None,  # Sample rate to use (optional).
    channels=None,  # Number of audio channels to use (optional).
  ):
    r'''
    Normalize the audio volume of a file.
    This function uses ffmpeg to normalize the audio volume of an audio file.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the normalized audio file.
      audioCodec (str): Audio codec to use (optional). If not provided, the default from configs will be used.
      audioFormat (str): Audio format to use (optional). If not provided, the default from configs will be used.
      audioBitrate (str): Audio bitrate to use (optional). If not provided, the default from configs will be used.
      normalizationFilter (str): Normalization filter to use (optional). If not provided, the default from configs will be used.
      sampleRate (int): Sample rate to use (optional). If not provided, the default from configs will be used.
      channels (int): Number of audio channels to use (optional). If not provided, the default from configs will be used.

    Returns:
      bool: True if normalization was successful, False otherwise.
    '''

    if (audioCodec is None):
      audioCodec = configs["ffmpeg"].get("audioCodec", "libmp3lame")
    if (audioFormat is None):
      audioFormat = configs["ffmpeg"].get("audioFormat", "mp3")
    if (audioBitrate is None):
      audioBitrate = configs["ffmpeg"].get("audioBitrate", "256k")
    if (normalizationFilter is None):
      normalizationFilter = configs["ffmpeg"].get("normalizationFilter", "loudnorm")
    if (sampleRate is None):
      sampleRate = configs["ffmpeg"].get("sampleRate", 44100)
    if (channels is None):
      channels = configs["ffmpeg"].get("channels", 2)

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", audioFilePath,  # Input audio file.
      "-c:a", audioCodec,  # Set the audio codec.
      "-f", audioFormat,  # Set the audio format.
      "-b:a", audioBitrate,  # Set the audio bitrate.
      "-af", normalizationFilter,  # Apply normalization filter.
      "-ar", str(sampleRate),  # Set the sample rate.
      "-ac", str(channels),  # Set the number of audio channels.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output normalized audio file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "NormalizeAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio normalization completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Audio normalization failed for: {audioFilePath}")
      return False

  async def GenerateSilentAudio(
    self,
    outputFilePath,  # Path to save the silent audio file.
    duration,  # Duration of the silent audio in seconds.
    audioCodec=None,  # Audio codec to use (optional).
    audioFormat=None,  # Audio format to use (optional).
    sampleRate=None,  # Sample rate to use (optional).
    channels=None,  # Number of audio channels to use (optional).
  ):
    r'''
    Generate a silent audio file of specified duration.
    This function uses ffmpeg to create a silent audio file with the specified parameters.

    Parameters:
      outputFilePath (str): Path to save the silent audio file.
      duration (int): Duration of the silent audio in seconds.
      audioCodec (str): Audio codec to use (optional). If not provided, the default from configs will be used.
      audioFormat (str): Audio format to use (optional). If not provided, the default from configs will be used.

    Returns:
      bool: True if the generation was successful, False otherwise.
    '''

    if (audioCodec is None):
      audioCodec = configs["ffmpeg"].get("audioCodec", "libmp3lame")
    if (audioFormat is None):
      audioFormat = configs["ffmpeg"].get("audioFormat", "mp3")
    if (sampleRate is None):
      sampleRate = configs["ffmpeg"].get("sampleRate", 44100)
    if (channels is None):
      channels = configs["ffmpeg"].get("channels", 2)

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-f", "lavfi",  # Use lavfi (libavfilter) to generate silence.
      "-i", "anullsrc",  # Use anullsrc filter to generate silent audio.
      "-t", str(duration),  # Set the duration of the silent audio.
      "-ar", str(sampleRate),  # Set the sample rate.
      "-ac", str(channels),  # Set the number of audio channels.
      "-acodec", audioCodec,  # Set the audio codec for silent audio.
      "-f", audioFormat,  # Set the audio format.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output audio file path.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "GenerateSilentAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Silent audio generated successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to generate silent audio for: {outputFilePath}")
      return False

  async def TrimAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the output audio file.
    start,  # Start time in seconds for the audio portion.
    end,  # End time in seconds for the audio portion.
  ):
    r'''
    Create a portion of an audio file from start to end time.
    This function uses ffmpeg to extract a portion of an audio file and save it to a new file.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the output audio file.
      start (int): Start time in seconds for the audio portion.
      end (int): End time in seconds for the audio portion.

    Returns:
      bool: True if the trim was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", audioFilePath,  # Input audio file.
      "-ss", str(start),  # Start time in seconds for the audio portion.
      "-to", str(end),  # End time in seconds for the audio portion.
      "-acodec", "copy",  # Copy the audio codec without re-encoding.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output audio file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "TrimAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio trimmed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to trim audio: {audioFilePath}")
      return False

  async def TrimVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the output video file.
    start,  # Start time in seconds for the video portion.
    end,  # End time in seconds for the video portion.
  ):
    r'''
    Create a portion of a video file from start to end time.
    This function uses ffmpeg to extract a portion of a video file and save it to a new file.

    Parameters:
      videoFilePath (str): Path to the input video file.
      outputFilePath (str): Path to save the output video file.
      start (int): Start time in seconds for the video portion.
      end (int): End time in seconds for the video portion.

    Returns:
      bool: True if the trim was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", videoFilePath,  # Input video file.
      "-ss", str(start),  # Start time in seconds for the video portion.
      "-to", str(end),  # End time in seconds for the video portion.
      # "-vf", f"scale={width}:{height}",  # Video filter to scale the video.
      "-r", str(configs["video"].get("fps", 30)),  # Set the frame rate.
      "-vcodec", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
      "-pix_fmt", configs["ffmpeg"].get("pixelFormat", "yuv420p"),  # Set the pixel format.
      "-acodec", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output video file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "TrimVideo")
    if (success):
      if (VERBOSE):
        logger.info(f"Video trimmed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to trim video: {videoFilePath}")
      return False

  async def ScaleVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the scaled video file.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    r'''
    Scale a video file to specified dimensions and frame rate.
    This function uses ffmpeg to resize a video file and save it to a new file.

    Parameters:
      videoFilePath (str): Path to the input video file.
      outputFilePath (str): Path to save the scaled video file.
      width (int): Width of the output video.
      height (int): Height of the output video.

    Returns:
      bool: True if the scaling was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", videoFilePath,  # Input video file.
      "-filter_complex",
      f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1/1,format=yuv420p[vout]",
      # Video filter to scale and pad the video with proper SAR.
      "-map", "[vout]",  # Map the filtered video.
      "-map", "0:a?",  # Map audio if it exists.
      "-r", str(configs["video"].get("fps", 30)),  # Set the frame rate.
      "-vcodec", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
      "-acodec", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
      "-ar", str(configs["ffmpeg"].get("sampleRate", 44100)),  # Set audio sample rate for consistency.
      "-ac", str(configs["ffmpeg"].get("channels", 2)),  # Set audio channels to stereo.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output video file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ScaleVideo")
    if (success):
      if (VERBOSE):
        logger.info(f"Video scaled successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to scale video: {randomVideoPath}")
      return False

  async def TrimScaleVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the scaled video file.
    start,  # Start time in seconds for the video portion.
    end,  # End time in seconds for the video portion.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    r'''
    Trim and scale a video file to specified dimensions and frame rate.
    This function uses ffmpeg to extract a portion of a video file, resize it, and save it to a new file.

    Parameters:
      videoFilePath (str): Path to the input video file.
      outputFilePath (str): Path to save the scaled video file.
      start (int): Start time in seconds for the video portion.
      end (int): End time in seconds for the video portion.
      width (int): Width of the output video.
      height (int): Height of the output video.

    Returns:
      bool: True if the merge was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", videoFilePath,  # Input video file.
      "-ss", str(start),  # Start time in seconds for the video portion.
      "-to", str(end),  # End time in seconds for the video portion.
      "-filter_complex",
      f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1/1,format=yuv420p[vout]",
      # Video filter to scale and pad the video with proper SAR.
      "-map", "[vout]",  # Map the filtered video.
      "-map", "0:a?",  # Map audio if it exists.
      "-r", str(configs["video"].get("fps", 30)),  # Set the frame rate.
      "-vcodec", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
      "-acodec", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
      "-ar", str(configs["ffmpeg"].get("sampleRate", 44100)),  # Set audio sample rate for consistency.
      "-ac", str(configs["ffmpeg"].get("channels", 2)),  # Set audio channels to stereo.
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output video file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "TrimScaleVideo")
    if (success):
      if (VERBOSE):
        logger.info(f"Video trimmed and scaled successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to trim and scale video: {randomVideoPath}")
      return False

  async def ConcatAudioFiles(
    self,
    audioFilePaths,  # List of paths to audio files to concatenate.
    outputFilePath,  # Path to save the concatenated audio file.
  ):
    r'''
    Concatenate multiple audio files into a single audio file.
    This function uses ffmpeg to filter and concatenate audio files.

    Parameters:
      audioFilePaths (list): List of paths to audio files to concatenate.
      outputFilePath (str): Path to save the concatenated audio file.

    Returns:
      bool: True if the merge was successful, False otherwise.
    '''

    try:
      # Create a temporary file with list of audio files (required for concat demuxer).
      with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for filePath in audioFilePaths:
          # Ensure we write absolute paths so ffmpeg can resolve them regardless of cwd.
          absPath = os.path.abspath(filePath)
          # Use forward slashes for ffmpeg on Windows and escape single quotes.
          ffPath = absPath.replace('\\', '/').replace("'", "'\"'\"'")
          f.write(f"file '{ffPath}'\n")
        fileListPath = f.name

      # Decide whether we can copy streams or need to re-encode.
      _, outExt = os.path.splitext(outputFilePath)
      outExt = outExt.lower()

      # Default ffmpeg settings from configs
      ffCfg = configs.get("ffmpeg", {})
      defaultCodec = ffCfg.get("audioCodec", "libmp3lame")
      defaultBitrate = ffCfg.get("audioBitrate", "256k")
      defaultSamplerate = ffCfg.get("sampleRate", 44100)
      defaultChannels = ffCfg.get("channels", 2)

      # If output is same container as inputs and codecs match, we could copy.
      # But to be safe across platforms and input types, re-encode when output extension is not the same
      # as the inputs' extensions or if output is a compressed format.
      inputExts = set([os.path.splitext(p)[1].lower() for p in audioFilePaths])

      reencode = True
      if len(inputExts) == 1 and outExt == list(inputExts)[0]:
        # Same extension for all inputs and output -> try copy.
        reencode = False

      if not reencode:
        ffmpegCommand = [
          "ffmpeg",
          "-f", "concat",
          "-safe", "0",
          "-i", fileListPath,
          "-c", "copy",
          "-preset", "fast",
          "-y",
          outputFilePath
        ]
      else:
        # Choose codec/format based on output extension.
        if outExt == ".mp3":
          audioCodec = "libmp3lame"
          # Use bitrate.
          codecArgs = ["-c:a", audioCodec, "-b:a", defaultBitrate]
        elif outExt == ".wav":
          audioCodec = "pcm_s16le"
          codecArgs = ["-c:a", audioCodec]
        elif outExt == ".ogg":
          audioCodec = "libvorbis"
          codecArgs = ["-c:a", audioCodec, "-b:a", defaultBitrate]
        else:
          # Generic fallback.
          audioCodec = defaultCodec
          codecArgs = ["-c:a", audioCodec, "-b:a", defaultBitrate]

        # Ensure sample rate and channels are set for re-encoding.
        codecArgs += ["-ar", str(defaultSamplerate), "-ac", str(defaultChannels)]

        ffmpegCommand = [
          "ffmpeg",
          "-f", "concat",
          "-safe", "0",
          "-i", fileListPath,
          *codecArgs,
          "-preset", "fast",
          "-y",
          outputFilePath
        ]

      # Run the ffmpeg command.
      success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ConcatAudioFiles")
      # Remove the temporary file list afterwards.
      try:
        if os.path.exists(fileListPath):
          os.remove(fileListPath)
      except Exception:
        pass

      if (success):
        return True
      else:
        return False
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Unexpected error in `ConcatAudioFiles`: {str(e)}")
      return False

  async def ConcatVideoFiles(
    self,
    videoFilePaths,  # List of paths to video files to concatenate.
    outputFilePath,  # Path to save the concatenated video file.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    r'''
    Concatenate multiple video files into a single video file.
    This function uses ffmpeg to concatenate video files using the concat demuxer.

    Parameters:
      videoFilePaths (list): List of paths to video files to concatenate.
      outputFilePath (str): Path to save the concatenated video file.
      width (int): Width of the output video.
      height (int): Height of the output video.

    Returns:
      bool: True if the merge was successful, False otherwise.
    '''

    try:
      # Build the list of input streams and scale filters
      inputs = []
      scales = []
      concats = []

      for i, filePath in enumerate(videoFilePaths):
        absPath = filePath.replace('\\', '/')
        inputs.extend(["-i", absPath])
        # Add setsar to ensure consistent SAR and handle audio channel issues.
        scales.append(
          f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1[vs{i}]; [vs{i}]format=yuv420p[v{i}]"
        )
        concats.append(f"[v{i}][{i}:a]")

      # Concat all scaled video/audio streams.
      scaleFilters = "; ".join(scales)
      concatInputs = "".join(concats)
      concatFilter = f"{scaleFilters}; {concatInputs}concat=n={len(videoFilePaths)}:v=1:a=1[outv][outa]"

      ffmpegCommand = [
        "ffmpeg",
        *inputs,
        "-filter_complex", concatFilter,
        "-map", "[outv]",
        "-map", "[outa]",
        "-r", str(configs["video"].get("fps", 30)),  # Set the frame rate.
        "-vcodec", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
        "-pix_fmt", configs["ffmpeg"].get("pixelFormat", "yuv420p"),  # Set the pixel format.
        "-acodec", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
        "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
        "-y",
        outputFilePath
      ]

      success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ConcatVideoFiles")
      if (success):
        if (VERBOSE):
          logger.info(f"Video concatenation completed successfully: {outputFilePath}")
        return True
      else:
        if (VERBOSE):
          logger.info(f"Video concatenation failed for: {videoFilePaths}")
        return False
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Unexpected error in `ConcatVideoFiles`: {str(e)}")
      return False

  async def TrimConcatVideoFiles(
    self,
    videoFilePaths,  # List of paths to video files to concatenate.
    outputFilePath,  # Path to save the concatenated video file.
    start,  # Start time in seconds for the video portion.
    end,  # End time in seconds for the video portion.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    r'''
    Concatenate multiple video files into a single video file, extracting a portion from each.
    Creates silent audio tracks for videos that don't have audio.
    This function uses ffmpeg to trim, scale, and concatenate video files.

    Parameters:
      videoFilePaths (list): List of paths to video files to concatenate.
      outputFilePath (str): Path to save the concatenated video file.
      start (int): Start time in seconds for the video portion.
      end (int): End time in seconds for the video portion.
      width (int): Width of the output video.
      height (int): Height of the output video.

    Returns:
      bool: True if the merge was successful, False otherwise.
    '''

    try:
      if (len(videoFilePaths) <= 1):
        success = await self.TrimScaleVideo(
          videoFilePaths[0],  # Only one video file, treat it as a single input.
          outputFilePath,
          start,
          end,
          width,
          height
        )
      else:

        # Create input arguments.
        inputs = []
        for filePath in videoFilePaths:
          absPath = filePath.replace('\\', '/')
          inputs.extend(["-i", absPath])

        # Build filter complex with audio fallback.
        filterParts = []
        concatInputs = []

        for i in range(len(videoFilePaths)):
          # Video trimming and scaling.
          format = configs["ffmpeg"].get("pixelFormat", "yuv420p")
          sampleRate = configs["ffmpeg"].get("sampleRate", 44100)
          filterParts.append(
            f"[{i}:v]trim=start={start}:end={end},"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1/1,format={format}[v{i}]"
          )

          # Check if audio exists.
          if (not self.IsFileSilent(videoFilePaths[i])):
            # Use existing audio.
            filterParts.append(
              f"[{i}:a]atrim=start={start}:end={end},"
              f"aresample={sampleRate},"
              f"pan=stereo|c0=c0|c1=c1[a{i}]"
            )
          else:
            # Create silent audio track with exact duration
            duration = float(end) - float(start)
            filterParts.append(
              f"aevalsrc=0:0:d={duration}:s={sampleRate},pan=stereo|c0=c0|c1=c1[a{i}]"
            )

          concatInputs.append(f"[v{i}][a{i}]")

        # Combine all filters.
        allFilters = "; ".join(filterParts)
        concatPart = "".join(concatInputs) + f"concat=n={len(videoFilePaths)}:v=1:a=1[outv][outa]"
        filterComplex = f"{allFilters}; {concatPart}"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as filterFile:
          filterFile.write(filterComplex)
          tempFilterFilePath = filterFile.name

        ffmpegCommand = [
          "ffmpeg",
          *inputs,  # Input video files.
          "-filter_complex_script", tempFilterFilePath,  # Use the filter complex from the temporary file.
          "-map", "[outv]",  # Map the output video stream.
          "-map", "[outa]",  # Map the output audio stream.
          "-r", str(configs["video"].get("fps", 30)),  # Set the frame rate.
          "-vcodec", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
          "-acodec", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
          "-ar", str(configs["ffmpeg"].get("sampleRate", 44100)),  # Set audio sample rate for consistency.
          "-ac", str(configs["ffmpeg"].get("channels", 2)),  # Set audio channels to stereo.
          "-pix_fmt", configs["ffmpeg"].get("pixelFormat", "yuv420p"),  # Set the pixel format.
          "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
          "-y",  # Overwrite output file without asking.
          outputFilePath
        ]

        success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "TrimConcatVideoFiles")
      if (success):
        if (VERBOSE):
          logger.info(f"Video concatenation with trimming completed successfully: {outputFilePath}")
        return True
      else:
        if (VERBOSE):
          logger.info(f"Video concatenation with trimming failed for: {videoFilePaths}")
        return False
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Unexpected error in `TrimConcatVideoFiles`: {str(e)}")
      return False

  async def MergeAudioVideoFiles(
    self,
    videoFilePath,  # Path to the input video file.
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the merged video file.
  ):
    r'''
    Merge an audio file with a video file.
    This function uses ffmpeg to combine an audio file with a video file.

    Parameters:
      videoFilePath (str): Path to the input video file.
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the merged video file.

    Returns:
      bool: True if the merge was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",  # Command to run ffmpeg.
      "-i", videoFilePath,  # Input video file.
      "-i", audioFilePath,  # Input audio file.
      "-c:v", configs["ffmpeg"].get("videoCodec", "libx264"),  # Set the video codec.
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),  # Set the audio codec.
      "-map", "0:v:0",  # Take video from first input (index 0, video stream 0).
      "-map", "1:a:0",  # Take audio from second input (index 1, audio stream 0).
      # Stop when the shortest stream ends. Other option is to use -t to specify duration. For example, -t 10 to limit the output to 10 seconds.
      "-shortest",
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",  # Overwrite output file without asking.
      outputFilePath  # Output merged video file.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "MergeAudioVideoFiles")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio and video merged successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to merge audio and video files: {videoFilePath}, {audioFilePath}")
      return False

  def GetCharactersWidth(self, size, baseFontSize):
    r'''
    Get the width of each printable ASCII character for a given font and size.
    This function uses PIL to create a font object and measure character widths.

    Parameters:
      size (int): Target size to calculate font size as a percentage.
      baseFontSize (str|int): Base font size as a percentage string (e.g., "6.8%") or fixed size in pixels.

    Returns:
      dict: A dictionary mapping each printable ASCII character to its width in pixels.
    '''

    fontPath = configs["ffmpeg"].get("captionFont", "Arial.ttf")

    if (isinstance(baseFontSize, str) and baseFontSize.endswith("%")):
      fontSizePercent = float(baseFontSize.rstrip("%"))
      fontSize = float(size * fontSizePercent / 100.0)
    else:
      fontSize = float(baseFontSize)

    try:
      font = ImageFont.truetype(fontPath, fontSize)
    except Exception as e:
      font = ImageFont.load_default()
      if (VERBOSE):
        logger.info(f"Font '{fontPath}' not found: {e}, using default font.")

    # Create image and draw context
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)

    # Get character widths
    charWidths = {}
    fallbackWidth = fontSize * 0.6

    for i in range(32, 127):
      char = chr(i).upper()  # Use uppercase for consistency.
      try:
        bbox = draw.textbbox((0, 0), char, font=font)
        width = bbox[2] - bbox[0]
        charWidths[char] = width
      except:
        if (VERBOSE):
          logger.info(f"Failed to measure width for character '{char}', using fallback width.")
        charWidths[char] = fallbackWidth

    return charWidths

  async def AddCaptionsToVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the output video file with captions.
    captionsList,  # A list of dictionaries containing caption text and timing.
    captionFontSize,  # Font size for captions.
  ):
    r'''
    Add word-by-word highlighted captions to a video file using ffmpeg.
    Each word is highlighted during its specific time window.

    Parameters:
      videoFilePath (str): Path to the input video file.
      outputFilePath (str): Path to save the output video file with captions.
      captionsList (list): A list of dictionaries containing caption words and timing.
      captionFontSize (str|int): Font size for captions as a percentage string (e.g., "5%") or fixed size in pixels.

    Returns:
      bool: True if captions were added successfully, False otherwise.
    '''

    # Get video dimensions.
    dimensions = self.GetFileDimensions(videoFilePath)
    if (dimensions is None):
      if (VERBOSE):
        logger.info(f"Failed to get video dimensions for: {videoFilePath}")
      return False
    videoWidth, videoHeight = dimensions

    fontType = configs["ffmpeg"].get("captionFont", "Arial")  # Default font type for captions.
    captionTextColor = configs["ffmpeg"].get("captionTextColor", "white")  # Default text color for captions.
    captionTextBorderColor = configs["ffmpeg"].get("captionTextBorderColor", "navy")  # Border color for caption text.
    captionTextBorderWidth = int(configs["ffmpeg"].get("captionTextBorderWidth", "2"))  # Border width for caption text.
    # Default highlighted text color.
    captionTextColorHighlighted = configs["ffmpeg"].get("captionTextColorHighlighted", "navy")
    # Border color for highlighted text.
    captionTextBorderColorHighlighted = configs["ffmpeg"].get("captionTextBorderColorHighlighted", "orange")
    # Caption position and offset. Position of captions (top, bottom, center).
    captionPosition = configs["ffmpeg"].get("captionPosition", "bottom")

    # Calculate relative font size (as percentage of video height).
    baseFontSize = captionFontSize  # configs["ffmpeg"].get("captionFontSize", "5%")
    if (isinstance(baseFontSize, str) and baseFontSize.endswith("%")):
      # Convert percentage to actual pixel size.
      fontSizePercent = float(baseFontSize.rstrip("%"))
      fontSize = str(int(videoWidth * fontSizePercent / 100))
    else:
      # Use fixed size if not percentage.
      fontSize = str(baseFontSize)

    # Border width for highlighted text.
    captionTextBorderWidthHighlighted = configs["ffmpeg"].get("captionTextBorderWidthHighlighted", "0.1%")
    if (isinstance(captionTextBorderWidthHighlighted, str) and captionTextBorderWidthHighlighted.endswith("%")):
      # Convert percentage based on the font size.
      captionTextBorderWidthPercent = float(captionTextBorderWidthHighlighted.rstrip("%"))
      captionTextBorderWidthHighlighted = str(float(float(fontSize) * captionTextBorderWidthPercent / 100))
    else:
      # Use fixed size if not percentage.
      captionTextBorderWidthHighlighted = str(captionTextBorderWidthHighlighted)

    if (VERBOSE):
      logger.info(f"Caption font size: {fontSize}")
      logger.info(f"Caption text border width: {captionTextBorderWidth}")
      logger.info(f"Caption text border width highlighted: {captionTextBorderWidthHighlighted}")

    captionPositionOffset = configs["ffmpeg"].get("captionPositionOffset", "15%")  # Offset for caption position.
    if (isinstance(captionPositionOffset, str) and captionPositionOffset.endswith("%")):
      # Convert percentage to actual pixel size.
      captionPositionOffsetPercent = float(captionPositionOffset.rstrip("%"))
      captionPositionOffset = str(int(videoHeight * captionPositionOffsetPercent / 100))
    else:
      # Use fixed size if not percentage.
      captionPositionOffset = str(captionPositionOffset)

    colors = configs.get("colors", ["blue"])
    if (captionTextBorderColorHighlighted == "random"):
      # Randomly choose a border color from the list.
      captionTextBorderColorHighlighted = random.choice(colors)

    # Validate caption position.
    if (captionPosition not in ["top", "bottom", "middle"]):
      # Randomly choose a position if not specified.
      captionPosition = random.choice(["top", "bottom", "middle"])

    # Calculate vertical position based on captionPosition setting.
    if (captionPosition == "bottom"):
      yPos = f"h-(text_h+{captionPositionOffset})"  # Bottom position.
    elif (captionPosition == "top"):
      yPos = f"{captionPositionOffset}"  # Top position.
    else:  # center
      yPos = f"(h-text_h)/2"  # Vertically centered position.

    # Base drawtext filters list.
    drawtextFilters = []

    totalNumberOfWords = sum(len(caption.get("words", [])) for caption in captionsList)
    if (VERBOSE):
      logger.info(f"Total number of words to process: {totalNumberOfWords}")

    # Get character widths for the font.
    charWidths = self.GetCharactersWidth(videoWidth, baseFontSize)
    if (VERBOSE):
      logger.info(f"Character widths for font '{fontType}': {charWidths}")

    # Escape font path for ffmpeg.
    escapedFontType = fontType.replace(':', '\\:')

    for j, caption in enumerate(captionsList):
      words = caption.get("words", [])
      if (not words):
        continue

      # Ensure words are sorted by start time.
      firstStart = np.round(words[0]["start"], 1)
      lastEnd = np.round(words[-1]["end"], 1)

      totalNumberOfSpaces = len(words) - 1  # Spaces between words.
      requiredWidth = sum([
        charWidths.get(c, 0)
        for c in "".join(wordInfo["word"].upper() for wordInfo in words)
      ]) + totalNumberOfSpaces * charWidths.get(" ", 0)
      remainingWidth = videoWidth - requiredWidth
      remainingHalfWidth = remainingWidth / 2.0
      # Calculate starting x position to center the entire phrase horizontally.
      startX = remainingHalfWidth
      currentX = 0

      # Generate drawtext filters for each word.
      for i, wordInfo in enumerate(words):
        # Remove single quotes and convert to uppercase.
        word = wordInfo["word"].upper().strip().replace("'", "")
        # word = EscapeText(word).strip()  # Escape text for ffmpeg.
        # word = word.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "; ")
        # # Escape special characters for ffmpeg.
        # word = re.escape(word)

        # Round start and end times to 2 decimal places.
        start = np.round(wordInfo["start"], 1)
        end = np.round(wordInfo["end"], 1)

        # Calculate x position for this word.
        xPos = startX + currentX

        if (VERBOSE):
          logger.info(f"Processing word: {word}, start: {start}, end: {end}")

        # Update current X position for next word.
        currentX += sum([
          charWidths.get(c, 0)
          for c in word
        ]) + charWidths.get(" ", 0)  # Add space width after the word.

        # 1. Normal text (visible throughout the video).
        # This filter draws the word at its position.
        normalFilter = (
          "drawtext=fontfile='" + escapedFontType + "':" +
          "fontsize=" + str(fontSize) + ":" +
          "text='" + word + "':" +
          "x=" + str(np.round(xPos, 2)) + ":" +
          "y=" + yPos + ":" +
          "fontcolor=" + captionTextColor + ":" +
          f"borderw={captionTextBorderWidth}:" +
          # Add border color for normal text.
          "bordercolor=" + captionTextBorderColor + ":" +
          "box=0:" +
          # Enable this text throughout the video.
          "enable='between(t\\," + str(firstStart) + "\\," + str(lastEnd) + ")'"
        )
        logger.info(normalFilter)
        drawtextFilters.append(normalFilter)

        # 2. Highlighted text (visible only during its time window).
        # This filter highlights the word during its specific time window.
        highlightFilter = (
          "drawtext=fontfile='" + escapedFontType + "':" +
          "fontsize=" + str(fontSize) + ":" +
          "text='" + word + "':" +
          "x=" + str(np.round(xPos, 2)) + ":" +
          "y=" + yPos + ":" +
          "fontcolor=" + captionTextColorHighlighted + ":" +
          f"borderw={captionTextBorderWidthHighlighted}:" +
          # Add border color for highlighted text.
          "bordercolor=" + captionTextBorderColorHighlighted + ":" +
          "box=0:" +
          "enable='between(t\\," + str(start) + "\\," + str(end) + ")'"
        )
        drawtextFilters.append(highlightFilter)

    # Combine all drawtext filters.
    vfFilter = ",".join(drawtextFilters)

    # Create a temporary file for the filter.
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as filterFile:
      filterFile.write(vfFilter)
      tempFilterFilePath = filterFile.name

    # videoFormat = configs["ffmpeg"].get("videoFormat", "mp4")

    ffmpegCommand = [
      "ffmpeg",
      "-i", videoFilePath,
      # "-vf", vfFilter,
      "-filter_complex_script", tempFilterFilePath,
      "-c:v", configs["ffmpeg"]["videoCodec"],
      "-c:a", configs["ffmpeg"]["audioCodec"],
      # "-f", "segment",
      # "-segment_time", str(1),  # Segment duration in seconds.
      # "-segment_format", videoFormat,  # Segment format.
      # "-reset_timestamps", "1",  # Reset timestamps for each segment.
      # "-segment_start_number", "0",  # Start from 0
      "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
      "-y",
      outputFilePath
      # .replace(f".{videoFormat}", f"_%03d.{videoFormat}")  # Output video file with segment numbering.
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "AddCaptionsToVideo")
    if (success):
      if (VERBOSE):
        logger.info(f"Captions added successfully to video: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Failed to add captions to video: {videoFilePath}")
      return False

  async def MixAudioFiles(
    self,
    audioFilePaths,  # List of paths to audio files to mix.
    outputFilePath,  # Path to save the mixed audio file.
    volumes=None,  # List of volume levels for each audio file (optional).
    duration="longest",  # Duration handling: "longest", "shortest", or "first".
  ):
    r'''
    Mix multiple audio files together (overlay, not concatenate).
    This function uses ffmpeg to combine multiple audio tracks simultaneously.

    Parameters:
      audioFilePaths (list): List of paths to audio files to mix.
      outputFilePath (str): Path to save the mixed audio file.
      volumes (list): List of volume levels for each audio file (optional). Default is 1.0 for all.
      duration (str): Duration handling - "longest", "shortest", or "first". Default is "longest".

    Returns:
      bool: True if the mix was successful, False otherwise.
    '''

    try:
      if (len(audioFilePaths) < 2):
        if (VERBOSE):
          logger.info("At least 2 audio files are required for mixing.")
        return False

      # Build input arguments.
      inputs = []
      for filePath in audioFilePaths:
        absPath = os.path.abspath(filePath).replace('\\', '/')
        inputs.extend(["-i", absPath])

      # Set default volumes if not provided.
      if (volumes is None):
        volumes = [1.0] * len(audioFilePaths)
      elif (len(volumes) != len(audioFilePaths)):
        if (VERBOSE):
          logger.info("Number of volume levels must match number of audio files.")
        return False

      # Build amix filter with volumes.
      volumeInputs = "".join([f"[{i}:a]volume={volumes[i]}[a{i}];" for i in range(len(audioFilePaths))])
      mixInputs = "".join([f"[a{i}]" for i in range(len(audioFilePaths))])
      amixFilter = f"{volumeInputs}{mixInputs}amix=inputs={len(audioFilePaths)}:duration={duration}:dropout_transition=2[aout]"

      ffmpegCommand = [
        "ffmpeg",
        *inputs,
        "-filter_complex", amixFilter,
        "-map", "[aout]",
        "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
        "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
        "-ar", str(configs["ffmpeg"].get("sampleRate", 44100)),
        "-ac", str(configs["ffmpeg"].get("channels", 2)),
        "-preset", "fast",
        "-y",
        outputFilePath
      ]

      success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "MixAudioFiles")
      if (success):
        if (VERBOSE):
          logger.info(f"Audio mixing completed successfully: {outputFilePath}")
        return True
      else:
        if (VERBOSE):
          logger.info(f"Audio mixing failed for: {audioFilePaths}")
        return False
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Unexpected error in `MixAudioFiles`: {str(e)}")
      return False

  async def ReduceNoise(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the noise-reduced audio file.
    noiseReduction=20,  # Noise reduction level in dB (optional).
  ):
    r'''
    Reduce background noise from an audio file.
    This function uses ffmpeg's afftdn (audio FFT denoiser) filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the noise-reduced audio file.
      noiseReduction (int): Noise reduction level in dB. Default is 20.

    Returns:
      bool: True if noise reduction was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", f"afftdn=nf=-{noiseReduction}",
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ReduceNoise")
    if (success):
      if (VERBOSE):
        logger.info(f"Noise reduction completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Noise reduction failed for: {audioFilePath}")
      return False

  async def RemoveSilence(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the audio file with silence removed.
    threshold=-50,  # Silence threshold in dB (optional).
    duration=0.5,  # Minimum silence duration in seconds (optional).
  ):
    r'''
    Remove silent portions from an audio file.
    This function uses ffmpeg's silenceremove filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the audio file with silence removed.
      threshold (int): Silence threshold in dB. Default is -50.
      duration (float): Minimum silence duration in seconds. Default is 0.5.

    Returns:
      bool: True if silence removal was successful, False otherwise.
    '''

    # Remove silence from start and end.
    silenceFilter = f"silenceremove=start_periods=1:start_threshold={threshold}dB:detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_threshold={threshold}dB:detection=peak,aformat=dblp,areverse"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", silenceFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "RemoveSilence")
    if (success):
      if (VERBOSE):
        logger.info(f"Silence removal completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Silence removal failed for: {audioFilePath}")
      return False

  async def EnhanceAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the enhanced audio file.
    bassGain=0,  # Bass boost level in dB (optional).
    trebleGain=0,  # Treble boost level in dB (optional).
  ):
    r'''
    Enhance audio with bass and treble adjustments.
    This function uses ffmpeg's bass and treble filters.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the enhanced audio file.
      bassGain (int): Bass boost level in dB (-20 to +20). Default is 0.
      trebleGain (int): Treble boost level in dB (-20 to +20). Default is 0.

    Returns:
      bool: True if enhancement was successful, False otherwise.
    '''

    filters = []
    if (bassGain != 0):
      filters.append(f"bass=g={bassGain}")
    if (trebleGain != 0):
      filters.append(f"treble=g={trebleGain}")

    if (not filters):
      # No enhancement needed, just copy.
      filters.append("anull")

    audioFilter = ",".join(filters)

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", audioFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "EnhanceAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio enhancement completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Audio enhancement failed for: {audioFilePath}")
      return False

  async def CompressAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the compressed audio file.
    threshold=-20,  # Compression threshold in dB (optional).
    ratio=4,  # Compression ratio (optional).
    attack=200,  # Attack time in ms (optional).
    release=1000,  # Release time in ms (optional).
    makeupGain=0,  # Makeup gain in dB (optional).
  ):
    r'''
    Apply dynamic range compression to audio.
    This function uses ffmpeg's acompressor filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the compressed audio file.
      threshold (int): Compression threshold in dB. Default is -20.
      ratio (int): Compression ratio. Default is 4.
      attack (int): Attack time in ms. Default is 200.
      release (int): Release time in ms. Default is 1000.
      makeupGain (int): Makeup gain in dB. Default is 0.

    Returns:
      bool: True if compression was successful, False otherwise.
    '''

    compressorFilter = f"acompressor=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}:makeup={makeupGain}dB"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", compressorFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "CompressAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio compression completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Audio compression failed for: {audioFilePath}")
      return False

  async def ConvertChannels(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the converted audio file.
    targetChannels=1,  # Target number of channels (1=mono, 2=stereo).
  ):
    r'''
    Convert audio between stereo and mono.
    This function uses ffmpeg's channel manipulation.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the converted audio file.
      targetChannels (int): Target number of channels (1=mono, 2=stereo). Default is 1.

    Returns:
      bool: True if conversion was successful, False otherwise.
    '''

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-ac", str(targetChannels),
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ConvertChannels")
    if (success):
      if (VERBOSE):
        logger.info(f"Channel conversion completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Channel conversion failed for: {audioFilePath}")
      return False

  async def LoopAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the looped audio file.
    loopCount=2,  # Number of times to loop (optional).
    totalDuration=None,  # Total duration in seconds (optional, overrides loopCount).
  ):
    r'''
    Create a looped audio file.
    This function uses ffmpeg to repeat audio multiple times.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the looped audio file.
      loopCount (int): Number of times to loop. Default is 2.
      totalDuration (float): Total duration in seconds (optional, overrides loopCount).

    Returns:
      bool: True if looping was successful, False otherwise.
    '''

    if (totalDuration is not None):
      # Calculate required loops based on duration.
      originalDuration = self.GetFileDuration(audioFilePath)
      if (originalDuration is None):
        if (VERBOSE):
          logger.info("Could not determine audio duration for looping.")
        return False
      loopCount = int(totalDuration / originalDuration) + 1

    ffmpegCommand = [
      "ffmpeg",
      "-stream_loop", str(loopCount - 1),  # -1 because original counts as 1.
      "-i", audioFilePath,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    if (totalDuration is not None):
      # Trim to exact duration.
      ffmpegCommand.insert(-2, "-t")
      ffmpegCommand.insert(-2, str(totalDuration))

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "LoopAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio looping completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Audio looping failed for: {audioFilePath}")
      return False

  async def ShiftPitch(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the pitch-shifted audio file.
    semitones=0,  # Number of semitones to shift (-12 to +12).
  ):
    r'''
    Shift the pitch of an audio file without changing speed.
    This function uses ffmpeg's asetrate and atempo filters.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the pitch-shifted audio file.
      semitones (int): Number of semitones to shift (-12 to +12). Default is 0.

    Returns:
      bool: True if pitch shifting was successful, False otherwise.
    '''

    if (semitones == 0):
      # No shift needed.
      import shutil
      shutil.copy(audioFilePath, outputFilePath)
      return True

    # Calculate pitch shift ratio.
    ratio = 2 ** (semitones / 12.0)
    sampleRate = configs["ffmpeg"].get("sampleRate", 44100)
    newRate = int(sampleRate * ratio)

    pitchFilter = f"asetrate={newRate},aresample={sampleRate},atempo=1.0"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", pitchFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ShiftPitch")
    if (success):
      if (VERBOSE):
        logger.info(f"Pitch shifting completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Pitch shifting failed for: {audioFilePath}")
      return False

  async def AddEcho(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the audio file with echo.
    delay=1000,  # Echo delay in ms (optional).
    decay=0.5,  # Echo decay (0.0 to 1.0) (optional).
  ):
    r'''
    Add echo effect to an audio file.
    This function uses ffmpeg's aecho filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the audio file with echo.
      delay (int): Echo delay in ms. Default is 1000.
      decay (float): Echo decay (0.0 to 1.0). Default is 0.5.

    Returns:
      bool: True if adding echo was successful, False otherwise.
    '''

    echoFilter = f"aecho=0.8:0.9:{delay}:{decay}"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", echoFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "AddEcho")
    if (success):
      if (VERBOSE):
        logger.info(f"Echo effect added successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Adding echo failed for: {audioFilePath}")
      return False

  async def AdjustStereoWidth(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the adjusted audio file.
    width=1.0,  # Stereo width (0.0 to 2.0) (optional).
  ):
    r'''
    Adjust the stereo width of an audio file.
    This function uses ffmpeg's stereotools filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the adjusted audio file.
      width (float): Stereo width (0.0=mono, 1.0=normal, 2.0=extra wide). Default is 1.0.

    Returns:
      bool: True if adjustment was successful, False otherwise.
    '''

    # Map width to mlev parameter (0-1 range, 0.5 is neutral).
    mlev = (2.0 - width) / 2.0

    stereoFilter = f"stereotools=mlev={mlev}"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-af", stereoFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "AdjustStereoWidth")
    if (success):
      if (VERBOSE):
        logger.info(f"Stereo width adjustment completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Stereo width adjustment failed for: {audioFilePath}")
      return False

  async def GenerateWaveform(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the waveform image.
    width=1280,  # Width of the waveform image (optional).
    height=240,  # Height of the waveform image (optional).
    colors="blue",  # Color scheme for the waveform (optional).
  ):
    r'''
    Generate a waveform image from an audio file.
    This function uses ffmpeg's showwavespic filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the waveform image.
      width (int): Width of the waveform image. Default is 1280.
      height (int): Height of the waveform image. Default is 240.
      colors (str): Color scheme for the waveform. Default is "blue".

    Returns:
      bool: True if waveform generation was successful, False otherwise.
    '''

    waveformFilter = f"showwavespic=s={width}x{height}:colors={colors}"

    ffmpegCommand = [
      "ffmpeg",
      "-i", audioFilePath,
      "-filter_complex", waveformFilter,
      "-frames:v", "1",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "GenerateWaveform")
    if (success):
      if (VERBOSE):
        logger.info(f"Waveform generation completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Waveform generation failed for: {audioFilePath}")
      return False

  async def GenerateSpectrum(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the spectrum video.
    width=1280,  # Width of the spectrum video (optional).
    height=720,  # Height of the spectrum video (optional).
    colorScheme="rainbow",  # Color scheme for the spectrum (optional).
  ):
    r'''
    Generate a spectrum analyzer video from an audio file.
    This function uses ffmpeg's showspectrum filter.

    Parameters:
      audioFilePath (str): Path to the input audio file.
      outputFilePath (str): Path to save the spectrum video.
      width (int): Width of the spectrum video. Default is 1280.
      height (int): Height of the spectrum video. Default is 720.
      colorScheme (str): Color scheme for the spectrum. Default is "rainbow".

    Returns:
      bool: True if spectrum generation was successful, False otherwise.
    '''

    # Create spectrum filter without unsupported 'rate' option, then add fps/format in chain.
    spectrumFilter = f"[0:a]showspectrum=s={width}x{height}:mode=combined:color={colorScheme}[vs]; [vs]fps=30,format=yuv420p[v]"

    # Build ffmpeg command for spectrum video generation (video + original audio).
    ffmpegCommand = [
      "ffmpeg",
      "-hide_banner", "-loglevel", "error",
      "-i", audioFilePath,
      "-filter_complex", spectrumFilter,
      "-map", "[v]",
      "-map", "0:a:0?",
      "-c:v", configs["ffmpeg"].get("videoCodec", "libx264"),
      "-c:a", configs["ffmpeg"].get("spectrumAudioCodec", "aac"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "192k"),
      "-preset", "fast",
      "-r", "30",
      "-pix_fmt", configs["ffmpeg"].get("pixelFormat", "yuv420p"),
      "-movflags", "+faststart",
      "-shortest",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "GenerateSpectrum")
    if (success and os.path.exists(outputFilePath) and os.path.getsize(outputFilePath) > 0):
      if (VERBOSE):
        logger.info(f"Spectrum generation completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Spectrum generation failed for: {audioFilePath}")
      return False

  async def CrossfadeAudio(
    self,
    firstAudioPath,  # Path to the first audio file.
    secondAudioPath,  # Path to the second audio file.
    outputFilePath,  # Path to save the crossfaded audio file.
    duration=3,  # Crossfade duration in seconds (optional).
  ):
    r'''
    Create a crossfade transition between two audio files.
    This function uses ffmpeg's acrossfade filter.

    Parameters:
      firstAudioPath (str): Path to the first audio file.
      secondAudioPath (str): Path to the second audio file.
      outputFilePath (str): Path to save the crossfaded audio file.
      duration (int): Crossfade duration in seconds. Default is 3.

    Returns:
      bool: True if crossfade was successful, False otherwise.
    '''

    crossfadeFilter = f"[0][1]acrossfade=d={duration}:c1=tri:c2=tri"

    ffmpegCommand = [
      "ffmpeg",
      "-i", firstAudioPath,
      "-i", secondAudioPath,
      "-filter_complex", crossfadeFilter,
      "-c:a", configs["ffmpeg"].get("audioCodec", "libmp3lame"),
      "-b:a", configs["ffmpeg"].get("audioBitrate", "256k"),
      "-preset", "fast",
      "-y",
      outputFilePath
    ]

    success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "CrossfadeAudio")
    if (success):
      if (VERBOSE):
        logger.info(f"Audio crossfade completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        logger.info(f"Audio crossfade failed for: {firstAudioPath}, {secondAudioPath}")
      return False

  def AnalyzeAudio(self, audioFilePath):
    r'''
    Analyze audio file and return comprehensive information.
    This function uses ffprobe to get detailed audio information.

    Parameters:
      audioFilePath (str): Path to the input audio file.

    Returns:
      dict: Dictionary containing audio information, or None if analysis fails.
    '''

    try:
      probe = ffmpeg.probe(audioFilePath)
      audioStream = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)

      if (audioStream is None):
        if (VERBOSE):
          logger.info("No audio stream found in file.")
        return None

      analysis = {
        "codec"        : audioStream.get("codec_name", "unknown"),
        "format"       : probe["format"].get("format_name", "unknown"),
        "duration"     : float(probe["format"].get("duration", 0)),
        "bitrate"      : int(probe["format"].get("bit_rate", 0)),
        "sampleRate"   : int(audioStream.get("sample_rate", 0)),
        "channels"     : int(audioStream.get("channels", 0)),
        "channelLayout": audioStream.get("channel_layout", "unknown"),
        "size"         : int(probe["format"].get("size", 0)),
      }

      # Get metadata if available.
      if ("tags" in probe["format"]):
        analysis["metadata"] = probe["format"]["tags"]

      return analysis
    except Exception as e:
      if (VERBOSE):
        logger.info(f"Error analyzing audio: {str(e)}")
      return None


if __name__ == "__main__":
  # Example usage of the functions.

  templatesPath = os.path.abspath("Assets")
  templatesVideos = configs["video"]["default"]
  templatesAudios = configs["audio"]["default"]
  outputDirPath = configs["storePath"]
  width4K = configs["video"]["width"]
  height4K = configs["video"]["height"]

  videoFiles = [os.path.join(templatesVideos, f) for f in os.listdir(templatesVideos)]
  random.shuffle(videoFiles)
  shuffledVideoFiles = videoFiles[:5]  # Select the first 5 video files.
  randomVideoPath = shuffledVideoFiles[0]  # Use the first video file for demonstration.

  audioFiles = [os.path.join(templatesAudios, f) for f in os.listdir(templatesAudios)]
  random.shuffle(audioFiles)
  shuffledAudioFiles = audioFiles[:5]  # Select the first 5 audio files.
  randomAudioPath = shuffledAudioFiles[0]  # Use the first audio file for demonstration.

  files = videoFiles + audioFiles  # Combine video and audio files for demonstration.
  random.shuffle(files)
  shuffledFiles = files[:5]  # Select the first 5 files for demonstration.

  obj = FFMPEGHelper()

  for file in shuffledFiles:
    print(f"Processing file: {file}")
    if (os.path.isfile(file)):
      size = obj.GetFileSize(file)
      print(f"- File Size: {size} bytes.")
      duration = obj.GetFileDuration(file)
      print(f"- File Duration: {np.round(duration, 2)} seconds.")
      isSilent = obj.IsFileSilent(file)
      print(f"- Is the file silent? {'Yes' if isSilent else 'No'}")
      hasAudioStream = obj.HasAudioStream(file)
      print(f"- Does the file have an audio stream? {'Yes' if hasAudioStream else 'No'}")

  totalDuration = obj.GetFilesDuration(files)
  print(f"Total Duration of all files: {np.round(totalDuration, 2)} seconds.")

  # # Test [NormalizeAudio] ===================================================================== #
  # outputAudioPath = os.path.join(outputDirPath, f"Normalized_{os.path.basename(randomAudioPath)}")
  # print(f"Normalizing audio file: {randomAudioPath}")
  # success = asyncio.run(
  #   obj.NormalizeAudio(
  #     audioFilePath=randomAudioPath,  # Path to the input audio file.
  #     outputFilePath=outputAudioPath,  # Path to save the normalized audio file.
  #   )
  # )
  # if (success):
  #   print(f"Audio normalized successfully: {outputAudioPath}")
  # else:
  #   print(f"Failed to normalize audio: {randomAudioPath}")
  # # =========================================================================================== #

  # # Test [GenerateSilentAudio] ================================================================ #
  # silentAudioPath = os.path.join(outputDirPath, "SilentAudio.mp3")
  # print(f"Generating silent audio file: {silentAudioPath}")
  # success = asyncio.run(
  #   obj.GenerateSilentAudio(
  #     outputFilePath=silentAudioPath,  # Path to save the silent audio file.
  #     duration=5,  # Duration of the silent audio in seconds.
  #   )
  # )
  # if (success):
  #   print(f"Silent audio generated successfully: {silentAudioPath}")
  # else:
  #   print(f"Failed to generate silent audio: {silentAudioPath}")
  # # =========================================================================================== #

  # # Test [TrimAudio] ========================================================================== #
  # outputAudioPath = os.path.join(outputDirPath, f"Trimmed_{os.path.basename(randomAudioPath)}")
  # print(f"Trimming audio file: {randomAudioPath}")
  # success = asyncio.run(
  #   obj.TrimAudio(
  #     audioFilePath=randomAudioPath,  # Path to the input audio file.
  #     outputFilePath=outputAudioPath,  # Path to save the output audio file.
  #     start=0,  # Start time in seconds for the audio portion.
  #     end=5,  # End time in seconds for the audio portion.
  #   )
  # )
  # if (success):
  #   print(f"Audio trimmed successfully: {outputAudioPath}")
  # else:
  #   print(f"Failed to trim audio: {randomAudioPath}")
  # # =========================================================================================== #

  # # Test [TrimVideo] ========================================================================== #
  # outputVideoPath = os.path.join(outputDirPath, f"Trimmed_{os.path.basename(randomVideoPath)}")
  # print(f"Trimming video file: {randomVideoPath}")
  # success = asyncio.run(
  #   obj.TrimVideo(
  #     videoFilePath=randomVideoPath,  # Path to the input video file.
  #     outputFilePath=outputVideoPath,  # Path to save the trimmed video file.
  #     start=0,  # Start time in seconds for the video portion.
  #     end=5,  # End time in seconds for the video portion.
  #   )
  # )
  # if (success):
  #   print(f"Video trimmed successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to trim video: {randomVideoPath}")
  # # =========================================================================================== #

  # # Test [ScaleVideo] ========================================================================= #
  # outputVideoPath = os.path.join(outputDirPath, f"Scaled_{os.path.basename(randomVideoPath)}")
  # print(f"Scaling video file: {randomVideoPath}")
  # success = asyncio.run(
  #   obj.ScaleVideo(
  #     videoFilePath=randomVideoPath,  # Path to the input video file.
  #     outputFilePath=outputVideoPath,  # Path to save the scaled video file.
  #     width=width4K // 4,  # Width of the output video. Scale down to 1/4 of 4K width.
  #     height=height4K // 4,  # Height of the output video. Scale down to 1/4 of 4K height.
  #   )
  # )
  # if (success):
  #   print(f"Video scaled successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to scale video: {randomVideoPath}")
  # # =========================================================================================== #

  # # Test [TrimScaleVideo] ===================================================================== #
  # outputVideoPath = os.path.join(outputDirPath, f"TrimmedScaled_{os.path.basename(randomVideoPath)}")
  # print(f"Trimming and scaling video file: {randomVideoPath}")
  # success = asyncio.run(
  #   obj.TrimScaleVideo(
  #     videoFilePath=randomVideoPath,  # Path to the input video file.
  #     outputFilePath=outputVideoPath,  # Path to save the scaled video file.
  #     start=0,  # Start time in seconds for the video portion.
  #     end=5,  # End time in seconds for the video portion.
  #     width=width4K // 4,  # Width of the output video. Scale down to 1/4 of 4K width.
  #     height=height4K // 4,  # Height of the output video. Scale down to 1/4 of 4K height.
  #   )
  # )
  # if (success):
  #   print(f"Video trimmed and scaled successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to trim and scale video: {randomVideoPath}")
  # # =========================================================================================== #

  # # Test [ConcatAudioFiles] =================================================================== #
  # outputAudioPath = os.path.join(outputDirPath, "ConcatenatedAudio.mp3")
  # print(f"Concatenating audio files: {shuffledAudioFiles}")
  # success = asyncio.run(
  #   obj.ConcatAudioFiles(
  #     audioFilePaths=shuffledAudioFiles,  # List of paths to audio files to concatenate.
  #     outputFilePath=outputAudioPath,  # Path to save the concatenated audio file.
  #   )
  # )
  # if (success):
  #   print(f"Audio files concatenated successfully: {outputAudioPath}")
  # else:
  #   print(f"Failed to concatenate audio files: {shuffledAudioFiles}")
  # # =========================================================================================== #

  # # Test [ConcatVideoFiles] =================================================================== #
  # outputVideoPath = os.path.join(outputDirPath, "ConcatenatedVideo.mp4")
  # print(f"Concatenating video files: {shuffledVideoFiles}")
  # success = asyncio.run(
  #   obj.ConcatVideoFiles(
  #     videoFilePaths=shuffledVideoFiles,  # List of paths to video files to concatenate.
  #     outputFilePath=outputVideoPath,  # Path to save the concatenated video file.
  #     width=width4K // 4,  # Width of the output video. Scale down to 1/4 of 4K width.
  #     height=height4K // 4,  # Height of the output video. Scale down to 1/4 of 4K height.
  #   )
  # )
  # if (success):
  #   print(f"Video files concatenated successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to concatenate video files: {shuffledVideoFiles}")
  # # =========================================================================================== #

  # # Test [TrimConcatVideoFiles] =============================================================== #
  # outputVideoPath = os.path.join(outputDirPath, "TrimmedConcatenatedVideo.mp4")
  # print(f"Trimming and concatenating video files: {shuffledVideoFiles}")
  # success = asyncio.run(
  #   obj.TrimConcatVideoFiles(
  #     videoFilePaths=shuffledVideoFiles,  # List of paths to video files to concatenate.
  #     outputFilePath=outputVideoPath,  # Path to save the concatenated video file.
  #     start=0,  # Start time in seconds for the video portion.
  #     end=5,  # End time in seconds for the video portion.
  #     width=width4K // 4,  # Width of the output video. Scale down to 1/4 of 4K width.
  #     height=height4K // 4,  # Height of the output video. Scale down to 1/4 of 4K height.
  #   )
  # )
  # if (success):
  #   print(f"Video files trimmed and concatenated successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to trim and concatenate video files: {shuffledVideoFiles}")
  # # =========================================================================================== #

  # # Test [MergeAudioVideoFiles] =============================================================== #
  # outputVideoPath = os.path.join(outputDirPath, "MergedAudioVideo.mp4")
  # print(f"Merging audio and video files: {randomVideoPath} with {randomAudioPath}")
  # success = asyncio.run(
  #   obj.MergeAudioVideoFiles(
  #     videoFilePath=randomVideoPath,  # Path to the input video file.
  #     audioFilePath=randomAudioPath,  # Path to the input audio file.
  #     outputFilePath=outputVideoPath,  # Path to save the merged video file.
  #   )
  # )
  # if (success):
  #   print(f"Audio and video merged successfully: {outputVideoPath}")
  # else:
  #   print(f"Failed to merge audio and video files: {randomVideoPath}, {randomAudioPath}")
  # # =========================================================================================== #

  # # Test [AddCaptionsToVideo] ================================================================= #
  # captionsList = [
  #   {
  #     "text" : "Hello world how are you",
  #     "words": [
  #       {"word": "Hello", "start": 1.0, "end": 1.5},
  #       {"word": "world", "start": 1.5, "end": 2.0},
  #       {"word": "how", "start": 2.0, "end": 2.5},
  #       {"word": "are", "start": 2.5, "end": 3.0},
  #       {"word": "you", "start": 3.0, "end": 3.5},
  #       {"word": "my", "start": 3.5, "end": 4.5},
  #       {"word": "friend", "start": 4.0, "end": 4.5},
  #     ]
  #   }
  # ]
  # outputVideoPath = os.path.join(outputDirPath, f"TrimmedScaled_{os.path.basename(randomVideoPath)}")
  # print(f"Trimming and scaling video file: {randomVideoPath}")
  # for (width, height) in [
  #   (width4K // 4, height4K // 4),
  #   (width4K // 2, height4K // 2),
  #   (width4K, height4K),
  # ]:
  #   print(f"Processing video with width: {width}, height: {height}.")
  #   success = asyncio.run(
  #     obj.TrimScaleVideo(
  #       videoFilePath=randomVideoPath,  # Path to the input video file.
  #       outputFilePath=outputVideoPath,  # Path to save the scaled video file.
  #       start=0,  # Start time in seconds for the video portion.
  #       end=5,  # End time in seconds for the video portion.
  #       width=width,  # Width of the output video. Scale down to 1/4 of 4K width.
  #       height=height,  # Height of the output video. Scale down to 1/4 of 4K height.
  #     )
  #   )
  #   if (success):
  #     print(f"Video trimmed and scaled successfully: {outputVideoPath}")
  #     captionedVideo = os.path.join(outputDirPath, f"GeneratedVideo_{width}_{height}.mp4")
  #     print(f"Adding captions to video: {outputVideoPath}")
  #     success = asyncio.run(
  #       obj.AddCaptionsToVideo(
  #         videoFilePath=outputVideoPath,  # Path to the input video file.
  #         outputFilePath=captionedVideo,  # Path to save the output video file with captions.
  #         captionsList=captionsList,  # A list of dictionaries containing caption text and timing.
  #       )
  #     )
  #     if (success):
  #       print(f"Captions added successfully to video: {captionedVideo}")
  #     else:
  #       print(f"Failed to add captions to video: {outputVideoPath}")
  #   else:
  #     print(f"Failed to trim and scale video: {randomVideoPath}")
  # # =========================================================================================== #
