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

import ffmpeg, os, time, random, yaml, hashlib, asyncio
from WhisperTranscribeHelper import WhisperTranscribeHelper
from TextToSpeechHelper import TextToSpeechHelper
from TextHelper import CleanText
from FFMPEGHelper import *

with open("configs.yaml", "r") as configFile:
  # Load the configuration from the YAML file.
  configs = yaml.safe_load(configFile)
VERBOSE = configs.get("verbose", False)  # Get the verbose setting from the configuration.


class VideoCreatorHelper(object):
  def __init__(self):
    """Initialize the VideoCreatorHelper with Whisper and TTS helpers."""

    # Initialize the Whisper transcription helper.
    self.whisperHelper = WhisperTranscribeHelper()
    # Initialize the Text-to-Speech helper.
    self.ttsHelper = TextToSpeechHelper()

    # Set the initial configurations for TTS and Whisper.
    self.ttsHelper.SetLanguage(configs["tts"]["language"])
    self.ttsHelper.SetVoice(configs["tts"]["voice"])
    self.whisperHelper.SetModelName(configs["whisper"]["modelName"])
    self.ffmpegHelper = FFMPEGHelper()

  def Text2Audio2TextTiming(
    self,
    text,
    workingPath=None,
    uniqueHashID=None,
    language=None,
    voice=None,
    speechRate=None,
  ):
    """Convert text to audio and then transcribe it to get timing information."""

    if (not workingPath):
      # If no working path is provided, use the default store path.
      workingPath = configs.get("storePath", "./Jobs")
      # Ensure the working path is an absolute path.
      workingPath = os.path.abspath(workingPath)

    dataList = []  # List to store transcriptions.
    # Generate audio from the provided text using the TTS helper.
    audios = self.ttsHelper.GenerateStoreSpeech(
      text,
      workingPath,
      audioFormat=configs["ffmpeg"].get("audioFormat", "mp3"),
      applyNormalization=configs["ffmpeg"].get("applyNormalization", True),
      uniqueHashID=uniqueHashID,
      language=language,
      voice=voice,
      speechRate=speechRate,
    )

    # Iterate over the generated audio data.
    for i, (generatedText, phonemes, audio, audioFilePath) in enumerate(audios):
      # Transcribe the generated audio to text.
      transcription = self.whisperHelper.Transcribe(
        audioFilePath, language=configs["whisper"].get("language", "en")
      )
      # Append the transcription to the list.
      dataList.append((generatedText, phonemes, audio, audioFilePath, transcription))
    # Return the list of transcriptions with timing information.
    return dataList

  def GetCurrentVideosList(self, videoType="Horizontal"):
    """Get the list of current videos in the default video directory."""
    # List all files in the default video directory.
    videosPath = configs["video"].get("default", "./Assets/Videos")
    if (videoType == "Vertical"):
      videosPath = os.path.join(videosPath, "Vertical Videos")
    else:
      videosPath = os.path.join(videosPath, "Horizontal Videos")
    currentVideosList = os.listdir(videosPath)
    # Filter out only video files (assuming they have specific extensions).
    # Convert allowed extensions to a tuple for filtering.
    videoExtensions = tuple(configs["video"].get("allowedExtensions", [".mp4", ".avi", ".mov", ".mkv"]))
    currentVideosList = [f for f in currentVideosList if f.lower().endswith(videoExtensions)]

    # Shuffle the list of video files to randomize their order.
    random.shuffle(currentVideosList)

    summary = []  # List to store video file paths and their durations.
    for videoFile in currentVideosList:
      videoFilePath = os.path.join(videosPath, videoFile)
      requiredDuration = configs["video"]["maxLengthPerVideo"]  # Maximum length of each video segment.
      if (os.path.isfile(videoFilePath)):
        # Get the duration of the video file using FFprobe.
        duration = self.ffmpegHelper.GetFileDuration(videoFilePath)
        if (duration >= requiredDuration):
          summary.append((videoFilePath, duration))

    return summary

  def GenerateVideo(
    self,
    text,
    language=None,
    voice=None,
    speechRate=None,
    videoQuality=None,
    videoType=None,
    uniqueHashID=None
  ):
    '''
    Generate a video with captions from the provided text.
    Parameters:
      text (str): The input text to convert to audio and captions.
      language (str): The language for TTS.
      voice (str): The voice for TTS.
      speechRate (float): The speech rate for TTS.
      videoQuality (str): The quality of the video (e.g., "4K" or "Full HD").
      videoType (str): The type of the video (e.g., "Horizontal" or "Vertical").
      uniqueHashID (str): A unique identifier for the job.
    Returns:
      (bool, str): A tuple indicating success and the generated video file name.
    '''

    if (not uniqueHashID):
      currentTime = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))  # Get the current time.
      # Create a unique hash ID for the text.
      uniqueHashID = hashlib.md5(text.encode() + currentTime.encode()).hexdigest()
      if (VERBOSE):
        print(f"Unique Hash ID for the text: {uniqueHashID}")

    storageFolder = configs.get("storePath", "./Jobs")  # Get the storage path from the configuration.
    storageFolder = os.path.abspath(storageFolder)  # Ensure the storage folder is an absolute path.
    os.makedirs(storageFolder, exist_ok=True)  # Ensure the storage folder exists.
    workingPath = os.path.join(storageFolder, uniqueHashID)  # Create a working path for the job.
    os.makedirs(workingPath, exist_ok=True)  # Ensure the working path exists.

    # Escaping text for safe processing.
    if (VERBOSE):
      print(f"Escaping text for processing: {text}")
    # Escape special characters in the text for safe processing.
    text = CleanText(text)

    if (VERBOSE):
      print(f"Processed text: {text}")
      print(f"Working path: {workingPath}")
      print(f"Unique Hash ID: {uniqueHashID}")
      print(f"Language: {language}, Voice: {voice}, Speech Rate: {speechRate}")

    if (not text or len(text.strip()) == 0):
      if (VERBOSE):
        print("No text provided for transcription after cleaning. Exiting.")
      return False, None

    # Get the transcription with timing.
    dataList = self.Text2Audio2TextTiming(
      text,
      workingPath=workingPath,
      uniqueHashID=uniqueHashID,
      language=language,
      voice=voice,
      speechRate=speechRate,
    )
    # Merge the transcribed audios into one.
    if (not dataList or (len(dataList) == 0)):
      if (VERBOSE):
        print("No transcriptions available. Exiting.")
      return False, None

    if (VERBOSE):
      print(f"Total transcriptions: {len(dataList)}")
      for i, (generatedText, phonemes, audio, audioFilePath, transcription) in enumerate(dataList):
        print(f"Transcription {i + 1}:")
        print(f"- Generated Text: {generatedText}")
        print(f"- Audio File Path: {audioFilePath}")
        print(f"- Transcription: {transcription}")

    captionWords = []
    # Add word-level captions to the video.
    timeOffset = 0.0  # Initialize time offset for captions.
    for i, (generatedText, phonemes, audio, audioFilePath, transcription) in enumerate(dataList):
      if (VERBOSE):
        print(f"Processing transcription {i + 1} with audio file: {audioFilePath}")
        print(f"Transcription: {transcription} | Duration: {transcription['duration']:.2f} seconds")
        print()
      # Create captions for each segment.
      for segment in transcription["segments"]:
        if (VERBOSE):
          print(f"Processing segment {i + 1}: {segment['text']}")
          print(f"Segment start: {segment['start']}, end: {segment['end']}")
          print()
        # segmentStart = segment["start"]  # Start time of the segment.
        words = segment["words"]  # Get the words in the segment.
        for word in words:
          if (VERBOSE):
            print(
              f"Word: {word['word']} | Start: {word['start']:.2f} | End: {word['end']:.2f} | Start': "
              f"{timeOffset + word['start']:.2f} | End': "
              f"{timeOffset + word['end']:.2f}"
            )
          # Create a caption entry for each word with its start and end times.
          captionWords.append(
            {
              "start": timeOffset + word["start"],
              "end"  : timeOffset + word["end"],  # Calculate the end time of the word.
              "word" : word["word"].strip(),  # Strip whitespace from the word.
            }
          )
      # Update the time offset with the end time of the last segment.
      timeOffset += transcription["duration"]
    if (VERBOSE):
      print(f"Total captions generated: {len(captionWords)}")

    # Determine video quality and type; and hence we can determine width and height.
    availableVideoQualities = configs["video"].get("availableQualities", [])
    qualityKeys = [quality[0] for quality in availableVideoQualities]

    availableVideoTypes = configs["video"].get("availableTypes", [])
    if (not videoQuality or (videoQuality not in qualityKeys)):
      videoQuality = "Full HD"  # Default to Full HD if not specified.
    if (not videoType or (videoType not in availableVideoTypes)):
      videoType = availableVideoTypes[0]
    if (VERBOSE):
      print(f"Video Quality: {videoQuality}, Video Type: {videoType}")
    width, height = availableVideoQualities[qualityKeys.index(videoQuality)][1]
    if (videoType == "Vertical"):
      width, height = height, width
    configs["video"]["width"] = width
    configs["video"]["height"] = height

    if (videoType == "Vertical"):
      captionFontSize = configs["ffmpeg"].get("verticalCaptionFontSize", "4.8%")  # Font size for captions.
    else:
      captionFontSize = configs["ffmpeg"].get("horizontalCaptionFontSize", "6.8%")  # Font size for captions.

    captionLineUsagePercentage = configs["ffmpeg"].get("captionLineUsagePercentage", 80)  # Line usage percentage.
    captionReservedWidth = (width * captionLineUsagePercentage) / 100  # Calculate reserved width for captions.

    charactersWidth = FFMPEGHelper().GetCharactersWidth(width, captionFontSize)

    if (VERBOSE):
      print(f"Video dimensions: {width}x{height}")
      print(f"Caption reserved width: {captionReservedWidth}")
      print(f"Caption font size: {captionFontSize}")
      print(f"Characters width mapping: {charactersWidth}")

    # Loop through the caption words and create a caption string. Process N words at a time.
    captionsList = []  # List to store caption strings.
    counter = 0
    wordWidth = 0
    # Loop through the caption words to create caption strings that fit within the reserved width.
    while (counter < len(captionWords)):
      currentWidth = 0
      i = counter
      while (i < len(captionWords)):
        currentWord = captionWords[i]["word"].upper()
        wordWidth = sum([charactersWidth.get(char, 0) for char in currentWord])
        if (VERBOSE):
          print(f"Word: {currentWord}, Width: {wordWidth}, Current Total Width: {currentWidth}")
        # Check if the current word alone exceeds the reserved width.
        if (wordWidth > captionReservedWidth):
          if (VERBOSE):
            print(f"Single word '{currentWord}' exceeds caption reserved width. Skipping this word.")
          break
        # Check if adding the current word along with the previous words exceeds the reserved width.
        if (currentWidth + wordWidth <= captionReservedWidth):
          currentWidth += wordWidth
          i += 1
        else:
          break
      if (VERBOSE):
        print(f"Words from index {counter} to {i} fit in the caption width.")
        print(f"Current width used: {currentWidth}, Reserved width: {captionReservedWidth}")
      firstWordIndex = counter
      lastWordIndex = i
      text = " ".join([word["word"] for word in captionWords[firstWordIndex:lastWordIndex]])
      captionsList.append({
        "text" : text,
        "words": captionWords[firstWordIndex:lastWordIndex],
      })
      counter = lastWordIndex

      if (wordWidth > captionReservedWidth):
        # If a single word alone exceeds the reserved width, add it alone and move to the next word.
        text = captionWords[counter]["word"]
        captionsList.append({
          "text" : text,
          "words": [captionWords[counter]],
        })
        counter += 1

    if (VERBOSE):
      print(f"Total caption strings generated: {len(captionsList)}")
      print(captionsList)

    # Get the audio format from the configuration.
    audioFormat = configs["ffmpeg"].get("audioFormat", "mp3")

    # Merge all audio files into one.
    mergedAudioPath = os.path.join(workingPath, f"{uniqueHashID}_Merged.{audioFormat}")
    inputAudioFiles = [audioFilePath for _, _, _, audioFilePath, _ in dataList]
    if (VERBOSE):
      print(f"Input audio files: {inputAudioFiles}")
    isDone = asyncio.run(
      self.ffmpegHelper.ConcatAudioFiles(
        inputAudioFiles,
        mergedAudioPath,
      )
    )
    if (not isDone):
      if (VERBOSE):
        print("Failed to merge audio files. Exiting.")
      return False, None

    audioDuration = self.ffmpegHelper.GetFileDuration(mergedAudioPath)
    if (VERBOSE):
      print(f"Merged audio file created at {mergedAudioPath} with duration {audioDuration:.2f} seconds.")
    if (audioDuration <= 0):
      if (VERBOSE):
        print("Merged audio file has zero duration. Exiting.")
      return False, None

    maxLengthPerVideo = configs["video"].get("maxLengthPerVideo", 5)  # Maximum length of each video segment.
    # Get the list of current videos and their durations.
    availableVideos = self.GetCurrentVideosList(videoType=videoType)
    requiredNoOfVideos = int(audioDuration / maxLengthPerVideo) + 1  # Calculate the number of videos needed.
    if (VERBOSE):
      print(f"Required number of videos: {requiredNoOfVideos} for audio duration {audioDuration:.2f} seconds.")

    if (requiredNoOfVideos <= 0):
      if (VERBOSE):
        print("No videos required for the given audio duration. Exiting.")
      return False, None
    elif (requiredNoOfVideos > len(availableVideos)):
      while (requiredNoOfVideos > len(availableVideos)):
        # If not enough videos are available, add more random videos.
        newVideos = self.GetCurrentVideosList(videoType)
        if (not newVideos):
          if (VERBOSE):
            print("No more videos available to add. Exiting.")
          return False, None
        availableVideos.extend(newVideos)

    videoFormat = configs["ffmpeg"].get("videoFormat", "mp4")  # Default video format.
    portionedOutputVideoPath = os.path.join(workingPath, f"{uniqueHashID}_Merged.{videoFormat}")

    # Get the absolute paths of the video files to concatenate.
    videoFilePaths = [os.path.abspath(videoFilePath) for videoFilePath, _ in availableVideos[:requiredNoOfVideos]]
    if (VERBOSE):
      print(portionedOutputVideoPath)
      print(videoFilePaths)

    isDone = asyncio.run(
      self.ffmpegHelper.TrimConcatVideoFiles(
        videoFilePaths=videoFilePaths,  # List of paths to video files to concatenate.
        outputFilePath=portionedOutputVideoPath,  # Path to save the concatenated video file.
        start=0,  # Start time in seconds for the video portion.
        end=maxLengthPerVideo,  # End time in seconds for the video portion.
        width=width,  # Width of the output video.
        height=height,  # Height of the output video.
      )
    )
    if (not isDone):
      if (VERBOSE):
        print("Failed to create video portion. Exiting.")
      return False, None
    if (VERBOSE):
      print(f"Video portion created at {portionedOutputVideoPath} with duration {audioDuration:.2f} seconds.")

    outputNoCaptionPath = os.path.join(workingPath, f"{uniqueHashID}_NoCaptions.{videoFormat}")
    isDone = asyncio.run(
      self.ffmpegHelper.MergeAudioVideoFiles(
        videoFilePath=portionedOutputVideoPath,  # Path to the video file.
        audioFilePath=mergedAudioPath,  # Path to the audio file.
        outputFilePath=outputNoCaptionPath,
      )
    )
    if (not isDone):
      if (VERBOSE):
        print("Failed to merge audio and video files. Exiting.")
      return False, None
    if (VERBOSE):
      print("Merged audio and video files successfully.")

    # Add captions to the video using FFmpeg.
    captionedVideoPath = os.path.join(workingPath, f"{uniqueHashID}_Final.{videoFormat}")
    # Add captions to the video using FFmpeg.
    isDone = asyncio.run(
      self.ffmpegHelper.AddCaptionsToVideo(
        videoFilePath=outputNoCaptionPath,  # Path to the input video file.
        outputFilePath=captionedVideoPath,  # Path to save the output video file with captions.
        captionsList=captionsList,  # A list of dictionaries containing caption text and timing.
        captionFontSize=captionFontSize,  # Font size for the captions.
      )
    )
    if (not isDone):
      if (VERBOSE):
        print("Failed to add captions to the video. Exiting.")
      return False, None
    if (VERBOSE):
      print(f"Video with captions created at {captionedVideoPath}.")

    if (VERBOSE):
      print("We are good.")

    # Clean up temporary files if needed.
    try:
      os.remove(mergedAudioPath)  # Remove the merged audio file.
      os.remove(portionedOutputVideoPath)  # Remove the video portion file.
      os.remove(outputNoCaptionPath)  # Remove the video without captions.
      # Remove audio files generated during the process.
      for _, _, _, audioFilePath, _ in dataList:
        if (os.path.exists(audioFilePath)):
          os.remove(audioFilePath)
          os.remove(audioFilePath.replace("Normalized_", ""))
    except Exception as e:
      if (VERBOSE):
        print(f"Error cleaning up temporary files: {e}")

    # Get the file name from the path.
    fileNameOnly = os.path.basename(captionedVideoPath)
    if (VERBOSE):
      print(f"Generated video file name: {fileNameOnly}")
    # Return True indicating the video was generated successfully, along with the file name.
    return True, fileNameOnly


if __name__ == "__main__":
  # Example usage of the VideoCreatorHelper class.
  videoCreator = VideoCreatorHelper()  # Initialize the video creator helper.

  # Sample text to convert to audio and transcribe.
  # sampleText = '''A Transformer sequence-to-sequence model is trained on various speech processing tasks,
  # including multilingual speech recognition, speech translation, spoken language identification,
  # and voice activity detection. These tasks are jointly represented as a sequence of tokens to be
  # predicted by the decoder, allowing a single model to replace many stages of a traditional speech-processing pipeline.
  # The multitask training format uses a set of special tokens that serve as task specifiers or classification targets.'''

  # sampleText = '''
  # [Artificial](/ˌɑɹtɪˈfɪʃəl/) [intelligence](/ɪnˈtɛlɪdʒəns/) (AI) represents the capability of computational systems to perform tasks traditionally associated with human intelligence.
  # These include [learning](/ˈlɝnɪŋ/), [reasoning](/ˈɹiːzənɪŋ/), [problem-solving](/ˈpɹɑbləmˌsɑlvɪŋ/), [perception](/pɚˈsɛpʃən/), and [decision-making](/dɪˈsɪʒənˌmeɪkɪŋ/).
  # As a field of [computer](/kəmˈpjuːtɚ/) [science](/ˈsaɪəns/), AI focuses on developing methods and software that enable machines to perceive their environment.
  # Machines use [learning](/ˈlɝnɪŋ/) and [intelligence](/ɪnˈtɛlɪdʒəns/) to take actions that maximize their chances of achieving defined [goals](/ɡoʊlz/).
  # The practical [applications](/ˌæplɪˈkeɪʃənz/) of AI are now ubiquitous in modern [technology](/tɛkˈnɑlədʒi/).
  # Many users may not recognize them as AI [systems](/ˈsɪstəmz/).
  # Examples include advanced web [search](/sɝtʃ/) engines like [Google](/ˈɡuːɡəl/) [Search](/sɝtʃ/).
  # [Recommendation](/ˌɹɛkəmɛnˈdeɪʃən/) [systems](/ˈsɪstəmz/) on [YouTube](/ˈjuːˌtjub/), [Amazon](/ˈæməzɑn/), and [Netflix](/ˈnɛtflɪks/).
  # '''

  # sampleText = '''
  # One key barrier to applying deep learning (DL) to omics and other biological datasets is data scarcity,
  # particularly when each gene or protein is represented by a single sequence.
  # This fundamental challenge is mainly relevant in research involving genetically constrained
  # organisms, organelles, specialized cell types, and biological cycles and pathways.
  # This study introduces a novel data augmentation strategy designed to facilitate the application of DL models to omics datasets.
  # This approach generated a high number of overlapping subsequences with controlled overlaps and shared nucleotide features through a sliding window technique.
  # A hybrid model of Convolutional Neural Network (CNN) and Long Short-Term Memory (LSTM) layers was applied
  # across augmented datasets comprising genes and proteins from eight microalgae and higher plant chloroplasts.
  # The data augmentation strategy enabled employing DL methods on these datasets and significantly improved the model performance by avoiding common issues
  # such as overfitting and non-representative sequence variations. The current augmentation process is highly adaptable,
  # providing flexibility across different types of biological data repositories.
  # Furthermore, a complementary k-mer-based data augmentation strategy was introduced for unlabeled datasets, enhancing unsupervised analysis.
  # Overall, these innovative strategies provide robust solutions for optimizing model training potential in the study of datasets with limited data availability.
  # '''

  # sampleText = '''This is a testing message that includes all special characters, numbers, and punctuation.
  # It contains numbers like 1234567890,
  # special characters like !@#$%^&*()_+-=~`|[]{}<>/\\
  # various symbols like ©®™,
  # and punctuation like . , ; : ? ! " '.
  # The goal is to ensure that the text-to-speech and transcription systems can handle various characters and formats.
  # The text also includes some emojis 😊👍, which should be processed correctly.
  # '''

  # sampleText = '''Accurate spatiotemporal traffic forecasting is critically important for optimizing intelligent resource management within 5G and future cellular networks.'''

  # sampleText = "Welcome to this!"
  sampleText = "Welcome to this! " * 10  # Repeat the text to increase its length.

  # Remove empty lines only.
  sampleText = "\n".join([line for line in sampleText.split("\n") if line.strip()])

  if (VERBOSE):
    print("Sample text to process:")
    print(sampleText.strip())

  # Generate a video from the provided text.
  isGenerated, videoID = videoCreator.GenerateVideo(sampleText.strip(), uniqueHashID="SampleVideoJob")
  if (not isGenerated):
    if (VERBOSE):
      print("Failed to generate video.")
  else:
    if (VERBOSE):
      print("Generated video:", videoID)
