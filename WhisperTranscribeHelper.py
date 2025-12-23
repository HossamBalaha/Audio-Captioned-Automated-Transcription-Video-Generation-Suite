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
import shutup

shutup.please()  # This function call suppresses unnecessary warnings.

# Import necessary libraries for the text-to-speech system.
import torch, os, time, whisper, yaml, logging
from FFMPEGHelper import FFMPEGHelper

# Use module logger so messages go through Python's logging system and appear with Flask output.
logger = logging.getLogger(__name__)

with open("configs.yaml", "r") as configFile:
  # Load the configuration from the YAML file.
  configs = yaml.safe_load(configFile)
VERBOSE = configs.get("verbose", False)  # Get the verbose setting from the configuration.


class WhisperTranscribeHelper(object):
  def __init__(self):
    """Initialize the WhisperTranscribeHelper with a specified model."""
    # Get a list of available Whisper models.
    self.availableModels = whisper.available_models()
    # Initialize the FFMPEG helper for audio processing.
    self.ffmpegHelper = FFMPEGHelper()

    # Default model name from the configuration.
    self.modelName = configs["whisper"].get("modelName", "base.en")
    self.SetModelName(self.modelName)  # Load the specified Whisper model.
    # Check if GPU is available, otherwise use CPU.
    self.device = "cuda" if (torch.cuda.is_available()) else "cpu"
    if (self.device == "cuda"):
      # Print the name of the GPU being used.
      logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
      # Indicate that the CPU is being used.
      logger.info("Using CPU for transcription.")

  def GetAvailableModels(self):
    """Return a list of available Whisper models."""
    # Return the list of available models.
    return self.availableModels

  def GetModelName(self):
    """Return the name of the currently loaded Whisper model."""
    # Return the name of the currently loaded model.
    return self.modelName

  def SetModelName(self, modelName):
    """Set the Whisper model to a new model name."""
    # Check if the requested model is available.
    if (modelName in self.availableModels):
      self.modelName = modelName  # Update the model name.
      self.model = whisper.load_model(modelName)  # Load the new model.
    else:
      # Raise an error if the model is not available.
      raise ValueError(f"Model {modelName} is not available.\nAvailable models: {self.availableModels}")

  def Transcribe(self, audioPath, language="en"):
    """Transcribe audio to text using the Whisper model."""
    # Load the audio file and process it for transcription.
    # Load the audio file into memory.
    audio = whisper.load_audio(audioPath)
    # Pad or trim the audio to fit the model's input requirements.
    audio = whisper.pad_or_trim(audio)

    # Make a prediction using the Whisper model.
    # Transcribe the audio to text in English.
    result = self.model.transcribe(
      audio,
      language=language,  # Specify the language for transcription.
      word_timestamps=True,  # Enable word-level timestamps.
    )

    # Get the duration of the audio file.
    audioDuration = self.ffmpegHelper.GetFileDuration(audioPath)

    # Process the result to extract relevant information.
    resultDict = {
      "text"    : result["text"],  # Extract the full transcribed text.
      "segments": [
        {
          "start": segment["start"],  # Start time of the segment.
          "end"  : segment["end"],  # End time of the segment.
          "text" : segment["text"],  # Text of the segment.
          "words": [
            {
              "word" : word["word"].strip(),  # Individual word.
              "start": word["start"],  # Start time of the word.
              "end"  : word["end"],  # End time of the word.
            }
            for word in segment["words"]  # Iterate over words in the segment.
          ],
        }
        for segment in result["segments"]  # Iterate over segments in the transcription.
      ],
      "language": result["language"],  # Extract the detected language.
      "duration": audioDuration,  # Duration of the audio in seconds.
    }

    # Return the transcription result as a dictionary.
    return resultDict


if __name__ == "__main__":
  # Example usage of the WhisperTranscribeHelper class.
  whisperTransObj = WhisperTranscribeHelper()  # Initialize the WhisperTranscribeHelper object.
  print("Available models:", whisperTransObj.GetAvailableModels())  # Display the list of available models.
  print("Current model:", whisperTransObj.GetModelName())  # Display the currently loaded model.
  audioFilePath = r"WRITE_CORRECT_PATH_HERE!"  # Path to the audio file for transcription.
  whisperTransObj.Transcribe(audioFilePath)  # Transcribe the audio file and display the results.
