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

shutup.please()  # This function call suppresses unnecessary warnings from libraries such as PyTorch.

# Import necessary libraries for the text-to-speech system.
import torch, os, time, random, asyncio, yaml
import soundfile as sf
from kokoro import KPipeline
from FFMPEGHelper import FFMPEGHelper

# Load configuration settings from the YAML file.
with open("configs.yaml", "r") as configFile:
  configs = yaml.safe_load(configFile)  # Parse the YAML configuration file.

# Get the verbose setting from the config. If not found, default to False.
VERBOSE = configs.get("verbose", False)


class TextToSpeechHelper(object):
  """A helper class for managing text-to-speech operations, including language and voice selection."""

  def __init__(self):
    """Initializes the TextToSpeechHelper with default settings and available language/voice options."""

    # Initialize a dictionary mapping language codes to their full names for user-friendly display.
    self.language2name = {
      "en-us": "American English",  # American English.
      "en-gb": "British English",  # British English.
      "es"   : "Spanish",  # Spanish.
      "fr"   : "French",  # French.
      "hi"   : "Hindi",  # Hindi.
      "it"   : "Italian",  # Italian.
      "ja"   : "Japanese",  # Japanese.
      "pt-br": "Brazilian Portuguese",  # Brazilian Portuguese.
      "zh"   : "Mandarin Chinese",  # Mandarin Chinese.
    }

    # Initialize a dictionary mapping language codes to their internal codes used by the TTS system.
    self.language2code = {
      "en-us": "a",  # American English.
      "en-gb": "b",  # British English.
      "es"   : "e",  # Spanish.
      "fr"   : "f",  # French.
      "hi"   : "h",  # Hindi.
      "it"   : "i",  # Italian.
      "ja"   : "j",  # Japanese (requires pip install misaki[ja]).
      "pt-br": "p",  # Brazilian Portuguese.
      "zh"   : "z",  # Mandarin Chinese (requires pip install misaki[zh]).
    }

    # List of available voice files for different languages and genders.
    self.voiceFiles = [
      # American English Female voices (11 voices).
      "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
      "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
      # American English Male voices (9 voices).
      "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam",
      "am_michael", "am_onyx", "am_puck", "am_santa",
      # British English Female voices (4 voices).
      "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
      # British English Male voices (4 voices).
      "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
      # Japanese voices (5 voices).
      "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo",
      # Mandarin Chinese voices (8 voices).
      "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi",
      "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang",
      # Spanish voices (3 voices).
      "ef_dora", "em_alex", "em_santa",
      # French voices (1 voice).
      "ff_siwis",
      # Hindi voices (4 voices).
      "hf_alpha", "hf_beta", "hm_omega", "hm_psi",
      # Italian voices (2 voices).
      "if_sara", "im_nicola",
      # Brazilian Portuguese voices (3 voices).
      "pf_dora", "pm_alex", "pm_santa"
    ]

    # Define a subset of English voices for random selection.
    self.englishVoices = self.voiceFiles[:20]  # First 20 voices are English.

    # Default settings for the TTS system, loaded from the configuration file.
    self.language = configs["tts"].get("language", "en-us")  # Default language is American English.
    self.langCode = self.language2code[self.language]  # Default language code.
    self.selectedVoice = configs["tts"].get("voice", "af_nova")  # Default voice is af_nova.
    self.speechRate = configs["tts"].get("speechRate", 1.0)  # Default speech rate.
    self.sampleRate = configs["tts"].get("sampleRate", 44100)  # Sample rate for audio processing.

  def GetAvailableLanguages(self):
    """Returns a dictionary of available languages mapped by their codes."""

    return self.language2name  # Return the dictionary of available languages.

  def GetAvailableVoices(self):
    """Returns a list of available voice files."""
    return self.voiceFiles  # Return the list of available voice files.

  def GetAvailableVoicesByLanguage(self):
    """Returns a dictionary of available voices categorized by language."""

    # Create a dictionary to hold voices categorized by language.
    voicesByLanguage = {
      "American English Female voices (11 voices)": self.voiceFiles[:11],  # First 11 voices.
      "American English Male voices (9 voices)."  : self.voiceFiles[11:20],  # Next 9 voices.
      "British English Female voices (4 voices)." : self.voiceFiles[20:24],  # Next 4 voices.
      "British English Male voices (4 voices)."   : self.voiceFiles[24:28],  # Next 4 voices.
      "Japanese voices (5 voices)."               : self.voiceFiles[28:33],  # Next 5 voices.
      "Mandarin Chinese voices (8 voices)."       : self.voiceFiles[33:41],  # Next 8 voices.
      "Spanish voices (3 voices)."                : self.voiceFiles[41:44],  # Next 3 voices.
      "French voices (1 voice)."                  : self.voiceFiles[44:45],  # Next 1 voice.
      "Hindi voices (4 voices)."                  : self.voiceFiles[45:49],  # Next 4 voices.
      "Italian voices (2 voices)."                : self.voiceFiles[49:51],  # Next 2 voices.
      "Brazilian Portuguese voices (3 voices)."   : self.voiceFiles[51:54]  # Last 3 voices.
    }
    return voicesByLanguage  # Return the categorized voices dictionary.

  def GetLanguageCode(self, langCode):
    """Returns the full name of the language corresponding to the given language code."""

    return self.language2name.get(
      langCode,  # Use the provided language code to look up the name.
      "Unknown Language"  # Default return value if the language code is not found.
    )  # Lookup the language name or return "Unknown Language".

  def GetSelectedLanguage(self):
    """Returns the currently selected language code."""

    return self.language  # Return the currently selected language.

  def GetSelectedVoice(self):
    """Returns the currently selected voice file."""

    return self.selectedVoice  # Return the currently selected voice.

  def GetSpeechRate(self):
    """Returns the current speech rate for the TTS system."""

    return self.speechRate  # Return the current speech rate.

  def SetLanguage(self, language):
    """Sets the language for the TTS pipeline and initializes the pipeline with the new language."""

    if (language not in list(self.language2code.keys())):  # Check if the language is supported.
      # Raise an error if the language is unsupported.
      raise ValueError(f"Unsupported language: {language}")
    self.langCode = self.language2code[language]  # Update the language code.
    self.language = language  # Update the selected language.
    # Initialize the TTS pipeline with the new language code.
    self.pipeline = KPipeline(lang_code=self.langCode, repo_id="hexgrad/Kokoro-82M")
    return self.pipeline  # Return the initialized pipeline.

  def SetVoice(self, voiceFile):
    """Sets the voice for the TTS pipeline. Supports random selection if 'random' is passed."""

    if (voiceFile == "random"):
      # Randomly select a voice from the available English voices.
      voiceFile = random.choice(self.englishVoices)
    if (voiceFile not in self.voiceFiles):  # Check if the voice file is supported.
      # Raise an error if the voice file is unsupported.
      raise ValueError(f"Unsupported voice file: {voiceFile}")
    self.selectedVoice = voiceFile  # Update the selected voice.
    return self.selectedVoice  # Return the updated voice.

  def GenerateYieldSpeech(self, text):
    """Generates speech from the given text using the selected voice and speech rate, yielding audio chunks."""
    # Set up the pipeline with the selected language and voice.
    self.pipeline = KPipeline(lang_code=self.langCode, repo_id="hexgrad/Kokoro-82M")

    # Generate speech using the pipeline.
    generator = self.pipeline(text, voice=self.selectedVoice, speed=self.speechRate)

    # Iterate over the generated speech chunks and yield them.
    for i, (generatedText, phonemes, audio) in enumerate(generator):
      # Yield each chunk of generated speech.
      yield generatedText, phonemes, audio

  def GenerateStoreSpeech(
    self,
    text,
    storePath,
    audioFormat="mp3",
    applyNormalization=True,
    uniqueHashID=None,
    language=None,
    voice=None,
    speechRate=None,
  ):
    """
    Generates speech from the given text and stores the audio data in the
    specified directory with optional normalization.
    Parameters:
      text (str): The text to convert to speech.
      storePath (str): The directory where the audio files will be stored.
      audioFormat (str): The format of the audio files (default is "mp3").
      applyNormalization (bool): Whether to apply normalization to the audio files (default is True).
      uniqueHashID (str): A unique identifier for the audio files
        (default is None, which will use the current timestamp).
      language (str): The language code for the TTS system (default is None, uses the current language).
      voice (str): The voice file to use for TTS (default is None, uses the current voice).
      speechRate (float): The speech rate for TTS (default is None, uses the current speech rate).
    Returns:
      list: A list of tuples containing the generated text, phonemes, audio data, and file paths.
    """

    # Check if the provided language is valid; if not, use the current language.
    if (language is not None):
      self.SetLanguage(language)  # Set the language if provided.
    if (voice is not None):
      self.SetVoice(voice)  # Set the voice if provided.
    if (speechRate is not None):
      self.speechRate = speechRate  # Set the speech rate if provided.

    # Define the file path for the audio file.
    if (uniqueHashID is None):
      uniqueHashID = time.strftime("%Y%m%d_%H%M%S")  # Get the current time as a string.

    # Generate speech using the helper method.
    f = self.GenerateYieldSpeech(text)
    audioData = []
    # Iterate over the generated speech chunks.
    for (generatedText, phonemes, audio) in f:
      # Store the generated data.
      audioData.append((generatedText, phonemes, audio))

    # Save the audio data to the specified path.
    # Iterate over the collected audio data.
    for i, (generatedText, phonemes, audio) in enumerate(audioData):
      audioFilePath = f"{storePath}/{uniqueHashID}_{i}.{audioFormat}"
      # Create the directory if it doesn't exist.
      os.makedirs(storePath, exist_ok=True)
      # Write the audio data to the file.
      sf.write(audioFilePath, audio, self.sampleRate)
      # If normalization is enabled, apply it to the audio data.
      if (applyNormalization):
        obj = FFMPEGHelper()
        normalizedAudioFilePath = f"{storePath}/Normalized_{uniqueHashID}_{i}.{audioFormat}"
        # Apply normalization to the audio file.
        success = asyncio.run(
          obj.NormalizeAudio(audioFilePath, normalizedAudioFilePath)
        )
        if (success):
          # If normalization was successful, update the file path.
          normalizedAudioFilePath = normalizedAudioFilePath
        else:
          # If normalization failed, keep the original file path.
          normalizedAudioFilePath = audioFilePath
      else:
        normalizedAudioFilePath = audioFilePath
      # Update the audio data with the file path.
      audioData[i] = (generatedText.strip(), phonemes, audio, normalizedAudioFilePath)

    # Return the list of audio data with file paths.
    return audioData  # Return the list of audio data with file paths.


# Example usage of the TextToSpeechHelper class.
if __name__ == "__main__":
  ttsHelper = TextToSpeechHelper()  # Initialize the TTS helper.

  # Display available languages and voices.
  print("Available Languages:", ttsHelper.GetAvailableLanguages())
  print("Available Voices:", ttsHelper.GetAvailableVoices())

  # Display the currently selected language and voice.
  print("Selected Language:", ttsHelper.GetSelectedLanguage())
  print("Selected Voice:", ttsHelper.GetSelectedVoice())

  # Set the language to American English and the voice to "af_heart".
  targetLanguage = configs["tts"].get("language", "en-us")  # Get the target language from configs.
  targetVoice = configs["tts"].get("voice", "af_nova")  # Get the target voice from configs.
  ttsHelper.SetLanguage(targetLanguage)  # Set to American English.
  ttsHelper.SetVoice(targetVoice)  # Set to a specific voice.

  # Display the updated selected language and voice.
  print("Selected Language:", ttsHelper.GetSelectedLanguage())
  print("Selected Voice:", ttsHelper.GetSelectedVoice())
  print("Selected Speech Rate:", ttsHelper.GetSpeechRate())

  # Generate and store speech for a sample text.
  text = "Hello, this is a test of the Kokoro TTS system."
  storePath = configs.get("storePath", "./Jobs")  # Get the store path from configs.
  audioFormat = configs["ffmpeg"].get("audioFormat", "mp3")  # Get the audio format from configs.
  applyNormalization = configs["ffmpeg"].get("applyNormalization", True)  # Get normalization setting from configs.
  ttsHelper.GenerateStoreSpeech(text, storePath, audioFormat=audioFormat, applyNormalization=applyNormalization)
  print(f"Speech generated and stored in {storePath}.")
