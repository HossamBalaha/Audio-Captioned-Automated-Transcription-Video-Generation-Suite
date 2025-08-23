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

import ffmpeg, subprocess, tempfile, yaml, os, random, asyncio, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from TextHelper import EscapeText

with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)

# Get the verbose setting from the config.
VERBOSE = configs.get("verbose", False)


class FFMPEGHelper(object):
  '''
  A helper class for FFMPEG operations.
  This class provides methods to perform various video and audio processing tasks using FFMPEG.
  '''

  def GetFileDuration(self, filePath):
    '''
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
        print("Function `GetFileDuration` encountered an error:")
        print(f"Error getting file duration: {e.stderr}")
      return None

  def GetFilesDuration(self, filePaths):
    '''
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
          print(f"Could not get duration for file: {filePath}")
          return None
    return totalDuration

  def GetFileSize(self, filePath):
    '''
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
        print("Function `GetFileSize` encountered an error:")
        print(f"Error getting file size: {str(e)}")
      return None

  def GetFileDimensions(self, filePath):
    '''
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
          print("No video stream found in the file.")
        return None
    except ffmpeg.Error as e:
      if (VERBOSE):
        print("Function `GetFileDimensions` encountered an error:")
        print(f"Error getting video dimensions: {e.stderr}")
      return None

  def IsFileSilent(self, filePath):
    '''
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
          print("No audio stream found in the video file.")
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
          print(f"Mean Volume: {meanVolume} dB")
        # Convert dB to a linear scale for comparison.
        meanVolume = 10 ** (meanVolume / 20)  # Convert dB to linear scale.
        if (VERBOSE):
          print(f"Mean Volume (linear scale): {meanVolume}")
        # Check if the mean volume is below the threshold.
        isSilent = (meanVolume < configs["ffmpeg"]["isSilentThreshold"])
        return isSilent
      else:
        if (VERBOSE):
          print("Could not determine the mean volume from the audio stream.")
        return False
    except ffmpeg.Error as e:
      if (VERBOSE):
        print("Function `IsFileSilent` encountered an error:")
        print(f"Error checking if video is silent: {e.stderr}")
      return False

  def HasAudioStream(self, filePath):
    '''
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
        print("Function `HasAudioStream` encountered an error:")
        print(f"Error checking audio stream: {e.stderr}")
      return False

  async def _ExecuteFFmpegCommand(self, command, functionName=""):
    '''
    Execute an FFMPEG command asynchronously.
    This method runs the provided FFMPEG command and returns the result.
    Parameters:
      command (list): List of command arguments for FFMPEG.
      functionName (str): Name of the function calling this method (for logging).
    Returns:
      bool: True if the command was successful, False otherwise.
      process: The subprocess object containing the result of the command.      
    '''
    try:
      if (VERBOSE):
        print(f"Executing command for `{functionName}`:\n{command}")
      process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
      )
      stdout, stderr = await process.communicate()
      if (process.returncode != 0):
        if (VERBOSE):
          print(f"Function `{functionName}` encountered an error:")
          print(f"Error executing command: {stderr.decode()}")
        return False, process
      else:
        if (VERBOSE):
          print(f"Command `{functionName}` executed successfully.")
        return True, process
    except Exception as e:
      if (VERBOSE):
        print(f"Function `{functionName}` encountered an error:")
        print(f"Error executing command: {str(e)}")
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
    '''
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
        print(f"Audio normalization completed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Audio normalization failed for: {audioFilePath}")
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
    '''
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
        print(f"Silent audio generated successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to generate silent audio for: {outputFilePath}")
      return False

  async def TrimAudio(
    self,
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the output audio file.
    start,  # Start time in seconds for the audio portion.
    end,  # End time in seconds for the audio portion.
  ):
    '''
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
        print(f"Audio trimmed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to trim audio: {audioFilePath}")
      return False

  async def TrimVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the output video file.
    start,  # Start time in seconds for the video portion.
    end,  # End time in seconds for the video portion.
  ):
    '''
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
        print(f"Video trimmed successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to trim video: {videoFilePath}")
      return False

  async def ScaleVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the scaled video file.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    '''
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
        print(f"Video scaled successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to scale video: {videoFilePath}")
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
    '''
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
        print(f"Video trimmed and scaled successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to trim and scale video: {videoFilePath}")
      return False

  async def ConcatAudioFiles(
    self,
    audioFilePaths,  # List of paths to audio files to concatenate.
    outputFilePath,  # Path to save the concatenated audio file.
  ):
    '''
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
      with tempfile.NamedTemporaryFile(mode="w", suffix='.txt', delete=False) as f:
        for filePath in audioFilePaths:
          # Use absolute paths and escape special characters.
          absPath = filePath.replace('\\', '/').replace("'", "'\"'\"'")
          f.write(f"file '{absPath}'\n")
        fileListPath = f.name

      ffmpegCommand = [
        "ffmpeg",  # Command to run ffmpeg.
        "-f", "concat",  # Use concat demuxer.
        "-safe", "0",  # Allow unsafe file paths.
        "-i", fileListPath,  # Input file list.
        "-c", "copy",  # Copy streams without re-encoding for speed.
        "-preset", "fast",  # Use a fast preset for encoding. It balances speed and quality.
        "-y",  # Overwrite output file without asking.
        outputFilePath  # Output audio file.
      ]
      # Run the ffmpeg command.
      success, process = await self._ExecuteFFmpegCommand(ffmpegCommand, "ConcatAudioFiles")
      if (success):
        return True
      else:
        return False
    except Exception as e:
      if (VERBOSE):
        print(f"Unexpected error in `ConcatAudioFiles`: {str(e)}")
      return False

  async def ConcatVideoFiles(
    self,
    videoFilePaths,  # List of paths to video files to concatenate.
    outputFilePath,  # Path to save the concatenated video file.
    width,  # Width of the output video.
    height,  # Height of the output video.
  ):
    '''
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
          print(f"Video concatenation completed successfully: {outputFilePath}")
        return True
      else:
        if (VERBOSE):
          print(f"Video concatenation failed for: {videoFilePaths}")
        return False
    except Exception as e:
      if (VERBOSE):
        print(f"Unexpected error in `ConcatVideoFiles`: {str(e)}")
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
    '''
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
          print(f"Video concatenation with trimming completed successfully: {outputFilePath}")
        return True
      else:
        if (VERBOSE):
          print(f"Video concatenation with trimming failed for: {videoFilePaths}")
        return False
    except Exception as e:
      if (VERBOSE):
        print(f"Unexpected error in `TrimConcatVideoFiles`: {str(e)}")
      return False

  async def MergeAudioVideoFiles(
    self,
    videoFilePath,  # Path to the input video file.
    audioFilePath,  # Path to the input audio file.
    outputFilePath,  # Path to save the merged video file.
  ):
    '''
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
        print(f"Audio and video merged successfully: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to merge audio and video files: {videoFilePath}, {audioFilePath}")
      return False

  def GetCharactersWidth(self, size, baseFontSize):
    '''
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
        print(f"Font '{fontPath}' not found: {e}, using default font.")

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
          print(f"Failed to measure width for character '{char}', using fallback width.")
        charWidths[char] = fallbackWidth

    return charWidths

  async def AddCaptionsToVideo(
    self,
    videoFilePath,  # Path to the input video file.
    outputFilePath,  # Path to save the output video file with captions.
    captionsList,  # A list of dictionaries containing caption text and timing.
    captionFontSize,  # Font size for captions.
  ):
    '''
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
        print(f"Failed to get video dimensions for: {videoFilePath}")
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
      print(f"Caption font size: {fontSize}")
      print(f"Caption text border width: {captionTextBorderWidth}")
      print(f"Caption text border width highlighted: {captionTextBorderWidthHighlighted}")

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
      print(f"Total number of words to process: {totalNumberOfWords}")

    # Get character widths for the font.
    charWidths = self.GetCharactersWidth(videoWidth, baseFontSize)
    if (VERBOSE):
      print(f"Character widths for font '{fontType}': {charWidths}")

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
          print(f"Processing word: {word}, start: {start}, end: {end}")

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
        print(normalFilter)
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
        print(f"Captions added successfully to video: {outputFilePath}")
      return True
    else:
      if (VERBOSE):
        print(f"Failed to add captions to video: {videoFilePath}")
      return False


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
