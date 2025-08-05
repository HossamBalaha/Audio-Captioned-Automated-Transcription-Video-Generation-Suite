'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Jun 2025
# Last Modification Date: Aug 1st, 2025
# Permissions and Citation: Refer to the README file.
'''

import yaml

configs = {
  "verbose"  : True,  # Enable verbose logging.
  "storePath": "./Jobs",
  "api"      : {
    "version"      : "v1",  # Version of the server.
    "port"         : 5000,  # Port on which the server will run.
    "maxJobs"      : 1,  # Maximum number of jobs that can be processed concurrently.
    "maxTextLength": 6500,  # Maximum length of text for processing.
    "maxTimeout"   : 10,  # Maximum timeout for job processing in seconds.
  },
  "tts"      : {
    "language"  : "en-us",  # Default language for TTS.
    "voice"     : "af_nova",  # Default voice for TTS.
    "sampleRate": 24000,  # Default sample rate for TTS.
    "speechRate": 1.0,  # Default speech rate for TTS.
  },
  "whisper"  : {
    # Models: whttps://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages
    "modelName": "turbo",  # Default model name for Whisper.
    "language" : "en"  # Default language for transcription.
  },
  "video"    : {
    "default"          : "./Assets/Videos",  # Default path for storing generated videos.
    # 4K resolution is 3840x2160, Full HD is 1920x1080, HD is 1280x720, 480p is 854x480.
    "width"            : 3840,  # Default video width.
    "height"           : 2160,  # Default video height.
    "fps"              : 30,  # Default frames per second for the video.
    "maxLengthPerVideo": 5,  # Maximum length of each video in seconds.
    "allowedExtensions": [".mp4", ".avi", ".mov", ".mkv"]  # Allowed video file extensions.
  },
  "audio"    : {
    "default"          : "./Assets/Audios",  # Default path for storing generated audio.
    "allowedExtensions": [".wav", ".mp3", ".ogg", ".flac"],  # Allowed audio file extensions.
  },
  "ffmpeg"   : {
    "isSilentThreshold"                       : 0.01,  # Threshold for silence detection in audio.
    # Default video codec for video. Options include libx264, libx265, etc.
    # libx264 is a widely used codec for video encoding.
    "videoCodec"                              : "libx264",
    # Default video bitrate for encoding. 5000k is a common choice for high-quality video.
    "videoBitrate"                            : "5000k",
    "videoFormat"                             : "mp4",  # Default video format for encoding.
    "pixelFormat"                             : "yuv420p",  # Default pixel format for video encoding.
    # Default audio codec for video processing.
    # "pcm_s16le" for WAV, "libvorbis" for OGG. "libmp3lame" for MP3.
    "audioCodec"                              : "libmp3lame",
    "audioFormat"                             : "mp3",  # Default audio format for encoding.
    "applyNormalization"                      : True,  # Whether to apply normalization to audio.
    "sampleRate"                              : 44100,  # Default sample rate for audio processing.
    "audioBitrate"                            : "256k",  # Default audio bitrate for encoding
    "channels"                                : 2,  # Number of audio channels.
    "normalizationFilter"                     : "loudnorm",  # Default normalization filter for audio.
    "fps"                                     : 30,  # Frames per second for video processing.

    # Caption settings for ffmpeg.
    "captionFont"                             : "./Assets/Fonts/Barlow_Condensed/BarlowCondensed-Bold.ttf",
    "captionsPerLine"                         : 5,  # Default number of captions per line.
    "captionPosition"                         : "middle",  # Default position for captions.
    "captionPositionOffset"                   : "15%",  # Default position for captions.
    "captionTextColor"                        : "white",  # Default text color for captions.
    "captionTextBorderColor"                  : "blue",  # Default text color for captions.
    "captionTextBorderWidth"                  : 2,  # Default border width for caption text.
    "captionTextColorHighlighted"             : "white",  # Default highlighted text color for captions.
    "captionTextBorderColorHighlighted"       : "random",  # Default color for captions.

    # Suitable for horizontal videos (16:9 aspect ratio).
    "captionFontSize"                         : "6.8%",  # Default font size for captions.
    "captionTextBorderWidthHighlighted"       : "13%",  # Default border width for highlighted captions.

    "defaultFont"                             : "./Assets/Fonts/Barlow_Condensed/BarlowCondensed-Bold.ttf",
    "defaultFontSize"                         : "6.8%",  # Default font size for captions.
    "defaultCaptionPosition"                  : "middle",  # Default position for captions.
    "defaultCaptionPositionOffset"            : "15%",  # Default position offset for captions.
    "defaultCaptionTextColor"                 : "white",  # Default text color for captions.
    "defaultCaptionTextBorderColor"           : "blue",  # Default text color for captions.
    "defaultCaptionTextBorderWidth"           : 2,  # Default border width for caption text.

    # Default highlighted caption settings.
    "defaultCaptionTextColorHighlighted"      : "white",
    "defaultCaptionTextBorderColorHighlighted": "random",

    # Default highlighted caption font size and border width.
    "defaultCaptionFontSizeHighlighted"       : "6.8%",
    "defaultCaptionTextBorderWidthHighlighted": "13%",

    # Default caption symbols to be used in the video.
    "captionSymbols"                          : [".", ",", ";", "-", "_", "'", "\""],

    # Default symbols that contradict with the FFmpeg captioning system.
    # These symbols will be escaped.
    "contradictingSymbols"                    : [
      "!", "?", ".", ",", ";", ":", "-", "_", "(", ")", "[", "]", "{", "}", "'", "\"", "…", "—", "–",
      ":", "!", "?", "…", "—", "–", "(", ")", "[", "]", "{", "}", "'", "\"", ":", ";", ",", "-", "_",
    ]
  },
  "colors"   : [
    "red", "green", "blue", "magenta", "black", "lightgray",
    "orange", "purple", "pink", "brown", "gray", "lightblue", "darkgreen",
  ],

}

with open("configs.yaml", "w") as configFile:
  # Save the configuration to a YAML file.
  yaml.dump(configs, configFile, default_flow_style=False)
