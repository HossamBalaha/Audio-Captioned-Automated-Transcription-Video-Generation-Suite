# Audio-Captioned Automated Transcription & Video Generation Suite

**Author:** Hossam Magdy Balaha  
**CV:** [hossambalaha.github.io](https://hossambalaha.github.io/)<br>
**GitHub:** [https://github.com/HossamBalaha](https://github.com/HossamBalaha)<br>
**Support Me:** [☕ Buy Me a Coffee](https://coff.ee/hossammbalaha)<br>
**Current Development Status:** Active<br>

<div style="text-align: center !important;" align="center">
<img src="/static/images/Logo.png" alt="Logo" width="500" align="center" style="text-align: center !important; align: center;">
</div>

---

## 📑 Table of Contents

- [📄 Overview](#-overview)
- [🎨 Web Interface](#-web-interface)
- [🤖 N8N Integration & Applicability](#-n8n-integration--applicability)
- [📁 Project Structure](#-project-structure)
- [🛠️ Preparation Steps](#️-preparation-steps)
- [🚀 Usage Instructions](#-usage-instructions)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [💖 Support](#-support)
- [📄 Copyright and License](#-copyright-and-license)
- [📬 Contact](#-contact)

## 📄 Overview

Audio-Captioned Automated Transcription & Video Generation Suite is a comprehensive, modular system designed to automate
the creation of professional-quality captioned videos from text or audio input. It integrates advanced AI and multimedia
technologies to deliver a seamless, scalable workflow for content creators, educators, developers, and automation
platforms like N8N.

**Key Features:**

- **End-to-End Automation:** Instantly transforms text or audio into synchronized, captioned videos with
  natural-sounding voiceovers, ready for social media, education, or marketing.
- **Speech & Transcription:** Utilizes Whisper for highly accurate speech-to-text transcription with word-level timing,
  enabling precise caption synchronization and multilingual support.
- **Text-to-Speech:** Integrates Kokoro TTS for customizable, high-quality voice generation, supporting multiple
  languages, voices, and adjustable speech rates.
- **Audio & Video Processing:** Employs FFmpeg for advanced audio normalization, silence detection, video trimming,
  merging, format conversion, and caption overlay.
- **RESTful API:** Exposes a robust Flask API for job submission, status tracking, asset management, and audio
  utilities (duration, size, silence check, normalization, conversion, and more).
- **Flexible Input/Output:** Supports a wide range of audio formats (MP3, WAV, OGG) and video qualities (4K, Full HD,
  etc.), with customizable backgrounds, fonts, and video types (horizontal/vertical).
- **Extensible & Modular:** Designed for easy integration, customization, and extension to fit diverse automation and
  media production needs, including seamless orchestration with N8N workflows.
- **Batch & Scalable Processing:** Enables batch job submission and scalable automation for large-scale media
  production, ideal for shorts, reels, and educational series.
- **Multi-Step Workflow Support:** Facilitates complex workflows such as transcription, TTS, video assembly, and
  automated publishing to platforms like YouTube, TikTok, or cloud storage.
- **Content Enrichment & Routing:** Supports content enrichment (e.g., auto-generated scripts, translation, branding)
  and conditional logic for error handling, notifications, and output routing.

**Workflow:**

1. Submit text or audio via API, web interface, or automated workflow (e.g., N8N).
2. System generates or transcribes audio, extracts timing, and selects background video assets.
3. Merges audio, video, and captions into a final, downloadable video file.
4. Provides additional audio tools for duration, size, silence detection, normalization, conversion, and more.
5. Enables automated publishing, notifications, and integration with third-party platforms via API or workflow tools.

Whether you need to batch-generate social media clips, automate educational content, build custom video pipelines, or
orchestrate media production with N8N, this suite offers a powerful foundation for scalable, AI-driven media automation.

---

## 🎨 Web Interface

The Audio-Captioned Automated Transcription & Video Generation Suite features a modern, user-friendly web interface
designed for seamless interaction and efficient workflow. Built with Flask and Bootstrap, the interface allows users to
easily submit jobs, manage video generation tasks, and utilize advanced audio tools; all from any device.

**Key Technologies:**

- Flask (Python web framework)
- Bootstrap (responsive UI)
- JavaScript (interactivity)
- HTML5 & CSS3

**User Experience Features:**

- Responsive design for desktop and mobile
- Intuitive navigation bar
- Expandable details and visual previews
- Real-time job status updates

### Index

The landing page provides an overview of the suite, quick access to main features, and a visually appealing
introduction.

<div style="text-align: center !important;" align="center">
<img src="/static/images/Index.png" 
alt="Logo" width="100%" align="center" style="text-align: center !important; align: center;">
</div>

### Text to Video

This page lets users submit text for automated video generation, select language, voice, video type, and quality.

<div style="text-align: center !important;" align="center">
<img src="/static/images/T2V%20Job%20Creation.png" 
alt="Text to Video" width="100%" align="center" style="text-align: center !important; align: center;">
</div>

### T2V Jobs Management

View, track, and manage all submitted video generation jobs, including their status and details.

<div style="text-align: center !important;" align="center">
<img src="/static/images/Text%20to%20Video%20(T2V)%20Jobs%20Management.png" 
alt="T2V Jobs Management" width="100%" align="center" style="text-align: center !important; align: center;">
</div>

### Audio Tools

Access advanced audio utilities such as duration, size, silence detection, and normalization.

<div style="text-align: center !important;" align="center">
<img src="/static/images/Audio%20Tools.png" 
alt="Audio Tools" width="100%" align="center" style="text-align: center !important; align: center;">
</div>

---

## 🤖 N8N Integration & Applicability

N8N is a powerful open-source workflow automation tool that can be seamlessly integrated with this suite to automate and
orchestrate media production tasks, including the creation of shorts, videos, and more. By leveraging N8N's visual
workflow builder and its extensive library of integrations, you can:

- **Automate Video Creation Pipelines:** Trigger video generation jobs from text or audio received via email, chat,
  webhooks, or other sources.
- **Batch Processing:** Schedule or batch-submit multiple jobs for automated captioned video creation, ideal for social
  media campaigns or educational content.
- **Multi-Step Workflows:** Chain together steps such as transcription, text-to-speech, video assembly, and delivery to
  platforms like YouTube, TikTok, or cloud storage.
- **API Integration:** Use N8N's HTTP Request node to interact with the suite's RESTful API endpoints for job
  submission, status tracking, and asset management.
- **Conditional Logic & Routing:** Build workflows that react to job status, errors, or content type, enabling advanced
  automation scenarios (e.g., send notifications when a video is ready, retry failed jobs, or route outputs to different
  destinations).
- **Content Enrichment:** Combine with other N8N nodes to enrich content (e.g., fetch trending topics, auto-generate
  scripts, translate captions, or add branding).
- **Scalable Automation:** Orchestrate large-scale media production by integrating with cloud storage, databases, and
  third-party services.

**Example N8N Workflow:**

1. **Trigger:** Receive new text or audio via webhook, email, or cloud upload.
2. **Submit Job:** Use HTTP Request node to POST to `/api/v1/jobs`.
3. **Monitor Status:** Poll `/api/v1/jobs/<jobId>` until completed.
4. **Download Result:** Fetch the final video via `/api/v1/jobs/<jobId>/result`.
5. **Publish/Distribute:** Upload to YouTube, TikTok, Google Drive, or send via email.
6. **Notify:** Send a Slack/Discord message or email when the job is done.

**Benefits of N8N Integration:**

- No-code/low-code automation for non-developers
- Visual workflow builder for rapid prototyping
- Connects with hundreds of services (cloud, social, productivity, AI)
- Enables scalable, repeatable, and error-resistant media production

For more details, see [N8N documentation](https://n8n.io/docs/) and explore how to connect this suite's API endpoints to
your automation workflows.

## 📁 Project Structure

```plaintext
├── configs.yaml               # Main configuration file
├── requirements.txt           # Python dependencies
├── Server.py                  # API server with endpoints
├── ConfigsSettings.py         # Configuration parser and manager
├── FFMPEGHelper.py            # FFMPEG wrapper for video/audio processing
├── TextToSpeechHelper.py      # TTS integration using Kokoro
├── WhisperTranscribeHelper.py # Whisper-based transcription
├── VideoCreatorHelper.py      # Core video assembly logic
├── TextHelper.py              # Cleaning and escaping text
├── Jobs/                      # Directory for job input/output files
│   ├── ef863../               # Example of a job directory
│   │   ├── job.json           # Job metadata
│   │   └── ef863.._Final.mp4  # Final video output
│   ├── e3r4e../               # Another job directory
│   └── ...                    # More job directories
├── Assets/                    # Static assets (images, background videos, etc.)
│   ├── Videos/                # Default background videos for video generation
│   │   ├── Horizontal Videos/ # Horizontal orientation videos
│   │   └── Vertical Videos/   # Vertical orientation videos
│   ├── Audios/                # Default audio files for testing the modules
│   └── Fonts/                 # Default fonts for captions
├── templates/                 # HTML templates for Flask webpage UIs
│   ├── index.html             # Main webpage template
│   ├── base.html              # Base template for all pages
│   ├── text2Video.html        # Text to video generation page
│   ├── audioTools.html        # Audio processing tools page
│   └── jobs.html              # Job management page template
├── static/                    # Static files for Flask (CSS, JS, images)
│   ├── css/                   # CSS files for styling
│   │   └── styles.css         # Main stylesheet
│   ├── js/                    # JavaScript files for interactivity
│   │   └── scripts.js         # Main script file
│   ├── images/                # Images used in the UI
│   │   └── logo.png           # Project logo
└── └── favicon.ico            # Favicon for the webpage
```

<details>
<summary>Click to expand project structure and details</summary>

### configs.yaml

The main configuration file containing all system settings:

- `verbose`: Enables detailed logging (true/false)
- `storePath`: Directory for storing job data ("./Jobs" by default)
- `api`: API settings including version, port, and maximum concurrent jobs
- `tts`: Text-to-speech settings (language, voice, sample rate, speech rate)
- `whisper`: Whisper transcription settings (model name, language)
- `video`: Video settings (resolution, FPS, maximum video segment length)
- `ffmpeg`: Audio/video encoding parameters

Example configuration:

```yaml
verbose: true
storePath: "./Jobs"
api:
  version: "v1"
  port: 5000
  maxJobs: 1
  maxTextLength: 2500
tts:
  language: "en-us"
  voice: "af_nova"
  sampleRate: 24000
  speechRate: 1.0
whisper:
  modelName: "turbo"
  language: "en"
video:
  default: "./Assets/Videos"
  type: "Horizontal"
  quality: "4K"
  fps: 30
  maxLengthPerVideo: 5
ffmpeg:
  audioFormat: "mp3"
  applyNormalization: true
  videoCodec: "libx264"
  audioCodec: "libmp3lame"
  pixelFormat: "yuv420p"
  sampleRate: 44100
  channels: 2
```

> **Notice**: These configurations are not the all settings available. More settings can be found and adjusted in
> `ConfigsSettings.py`. Each setting is documented in the file.

### Jobs Directory

Stores all job-related data including:

- Audio files generated from text.
- Video files with captions.
- Transcription data with timing information.
- Job status information.
- Temporary processing files.
- Temporary files are cleaned up after processing is complete.

### Assets Directory

Contains background video assets used in the final video creation:

- Default video assets in `"./Assets/Videos/Horizontal Videos"` and
  `"./Assets/Videos/Vertical Videos"`
- Users can add their own videos to these directories.
- System expects these videos to be of high quality (4K by default)
- Each video segment is used for a fixed duration (`maxLengthPerVideo`)

### FFMPEGHelper.py

Provides comprehensive FFmpeg operations for audio/video processing:

- `GetFileDuration(filePath)`: Retrieves media file duration
- `NormalizeAudio(audioFilePath, outputFilePath)`: Normalizes audio volume levels
- `TrimVideo(videoFilePath, outputFilePath, start, end)`: Extracts specific video segments
- `MergeAudioVideoFiles(videoFilePath, audioFilePath, outputFilePath)`: Combines audio and video
- `AddCaptionsToVideo(videoFilePath, outputFilePath, captionsList)`: Adds timed captions to video
- `GenerateSilentAudio(outputFilePath, duration)`: Creates silent audio tracks
- `IsFileSilent(filePath)`: Checks if a video has audio
- `HasAudioStream(filePath)`: Verifies presence of audio streams

### TextToSpeechHelper.py

Handles text-to-speech conversion using Kokoro TTS:

- Language and voice selection system.
- Audio generation with configurable sample rate.
- Audio normalization for consistent volume.
- Support for multiple audio formats (MP3, WAV, etc.).

Key methods:

- `SetLanguage(language)`: Changes the TTS language
- `SetVoice(voice)`: Changes the TTS voice
- `GenerateStoreSpeech(text, workingPath, audioFormat, applyNormalization)`: Generates speech from text and stores the
  audio file
- `GetAvailableLanguages()`: Returns supported languages
- `GetAvailableVoices()`: Returns voices available for current language

### VideoCreatorHelper.py

Core video generation component that coordinates all processes:

- Converts text to speech and gets precise timing information.
- Selects appropriate background videos based on audio duration.
- Merges audio with video segments.
- Adds captions synchronized with speech.
- Handles the complete video creation pipeline.

Key methods:

- `Text2Audio2TextTiming(text, workingPath, uniqueHashID)`: Converts text to audio and returns timing information.
- `GetCurrentVideosList()`: Gets available background videos with their durations.
- `GenerateVideo(text, uniqueHashID)`: Main method that creates the complete video.
- `MergeAudioVideoFiles(videoFilePath, audioFilePath, outputFilePath)`: Combines audio and video.

### WhisperTranscribeHelper.py

Handles audio transcription with word-level timing:

- Supports all Whisper models (tiny, base, small, medium, large, turbo).
- Provides precise word timing for caption synchronization.
- Handles audio file processing and transcription.

Key methods:

- `SetModelName(modelName)`: Changes the Whisper model.
- `Transcribe(audioFilePath, language=None)`: Transcribes audio file and returns text with timing.
- `GetAvailableModels()`: Lists all available Whisper models.

### Server.py (API Documentation)

<details>
<summary>API Endpoints</summary>

Flask-based REST API server with the following endpoints:

#### GET `/api/v1/status`

Returns the current status of the server.

- **Response** (JSON):
  ```json
  {
    "status": "Server is running"
  }
  ```

#### GET `/api/v1/ready`

Checks if the server is ready to accept jobs.

- **Response** (JSON):
  ```json
  {
    "ready": true
  }
  ```

- **Status Codes**:
    - `200 OK`: Server is ready.
    - `503 Service Unavailable`: Server is not ready.

#### GET `/api/v1/languages`

Lists available TTS languages.

- **Response** (JSON):
  ```json
  {
    "languages": {
        "en-gb": "British English",
        "en-us": "American English",
        "es": "Spanish",
        "fr": "French",
        "hi": "Hindi",
        "it": "Italian",
        "ja": "Japanese",
        "pt-br": "Brazilian Portuguese",
        "zh": "Mandarin Chinese"
    }
  }
  ```

- **Status Codes**:
    - `200 OK`: Languages retrieved successfully.

#### GET `/api/v1/voices`

Lists available TTS voices for the current language.

- **Request Header**:
    - `type`: The type of the output whether its list or dictionary. It can be `list` or `dict`.

- **Response** (JSON if `type` is `list`):
  ```json
  {
    "voices": [
        "af_heart",
        "af_alloy",
        "af_aoede",
        "af_bella",
        "af_jessica",
        "af_kore",
        "af_nicole",
        "af_nova",
        "af_river",
        "af_sarah",
        "af_sky",
        ...
    ]
  }
  ```

- **Response** (JSON if `type` is `dict`):
  ```json
  {
    "voices": {
        "American English Female voices (11 voices)": [
            "af_heart",
            "af_alloy",
            "af_aoede",
            "af_bella",
            "af_jessica",
            "af_kore",
            "af_nicole",
            "af_nova",
            "af_river",
            "af_sarah",
            "af_sky"
        ],
        ...
    }
  }
  ```

- **Status Codes**:
    - `200 OK`: Voices retrieved successfully.

#### GET `/api/v1/videoTypes`

Lists available video types.

- **Response** (JSON):
  ```json
  {
    "videoTypes": [
        "Horizontal",
        "Vertical"
    ]
  }
  ```

- **Status Codes**:
    - `200 OK`: Video types retrieved successfully.

#### GET `/api/v1/videoQualities`

Lists available video qualities.

- **Response** (JSON):
  ```json
  {
    "videoQualities": [
        [
            "4K",
            [
                3840,
                2160
            ]
        ],
        [
            "Full HD",
            [
                1920,
                1080
            ]
        ],
        ...
    ]
  }
  ```

- **Status Codes**:
    - `200 OK`: Video qualities retrieved successfully.

#### GET `/api/v1/jobs`

Gets a list of all submitted jobs including their details such as text, status, language, voice, etc.

- **Response** (JSON):
  ```json
  {
    "jobs": [
        {
            "createdAt": "2025-08-08 22:15:27",
            "isCompleted": true,
            "jobId": "07abdf3f0600152a9d0d01eab9769092",
            "language": "en-gb",
            "speechRate": 1,
            "status": "completed",
            "text": "Select the suitable voice according to the language you selected. For example, if you selected American English, you should select an American English voice. You will find the groups highlighted in the voice selection dropdown.",
            "videoQuality": "HD",
            "videoType": "Horizontal",
            "voice": "af_heart"
        },
        {
            "createdAt": "2025-08-08 22:15:48",
            "isCompleted": true,
            "jobId": "304c34066273fe14790873de94f30346",
            "language": "en-gb",
            "speechRate": 1,
            "status": "completed",
            "text": "Select the suitable voice according to the language you selected. For example, if you selected American English, you should select an American English voice. You will find the groups highlighted in the voice selection dropdown.",
            "videoQuality": "HD",
            "videoType": "Vertical",
            "voice": "af_heart"
        },
        ...
    ]
  }
  ```

- **Status Codes**:
    - `200 OK`: Jobs retrieved successfully.

#### POST `/api/v1/jobs`

Submits a new job for video generation.

- **Request Body** (form-data):
    - `text`: The text to convert into a video.
    - `language`: (Optional) TTS language code (default: "en-us").
    - `voice`: (Optional) TTS voice ID (default: "af_nova").
    - `speechRate`: (Optional) TTS speech rate (default: 1.0).
    - `videoType`: (Optional) Video type ("Horizontal" or "Vertical", default: "Horizontal").
    - `videoQuality`: (Optional) Video quality ("4K", "Full HD", etc., default: "4K").

- **Response** (JSON):
  ```json
  {
    "jobId": "5d8279821d778604193ab2f6e4e39264"
  }
  ```

- **Status Codes**:
    - `202 Accepted`: Job successfully submitted.
    - `400 Bad Request`: Invalid input data (e.g., text too long).

#### GET `/api/v1/jobs/<jobId>`

Checks the status of a video generation job. The status can be one of the following:

- `processing`: The job is currently being processed.
- `completed`: The job has been completed successfully.
- `failed`: The job has failed during processing.
- `queued`: The job is queued and waiting to be processed.

- **Response** (JSON):
  ```json
  {
    "createdAt": "2025-08-08 22:21:53",
    "jobId": "5d8279821d778604193ab2f6e4e39264",
    "language": "en-us",
    "speechRate": 1,
    "status": "completed",
    "text": "This project is a fully automated video creation pipeline that utilizes state-of-the-art AI tools for transcription,\ntext-to-speech, and video/audio processing. It integrates Whisper for speech-to-text, Kokoro TTS for voice generation,\nFFMPEG for video/audio manipulation, and Rust-powered build tools via Cargo — all orchestrated through a Python backend.\nPerfect for content creators, educators, or developers looking to automate short video generation from scripts or audio\ninputs.",
    "videoQuality": "4K",
    "videoType": "Vertical",
    "voice": "af_nicole"
  }
  ```

- **Status Codes**:
    - `200 OK`: Job status retrieved successfully.
    - `404 Not Found`: Job ID does not exist.

#### GET `/api/v1/jobs/<jobId>/result`

Downloads the completed video file.

- **Response**: The video file as an attachment.

- **Status Codes**:
    - `200 OK`: Video file retrieved successfully.
    - `404 Not Found`: Job ID does not exist or job is not completed.
    - `400 Bad Request`: Job is not yet completed.
    - `500 Internal Server Error`: Error retrieving the video file.

#### DELETE `/api/v1/jobs/<jobId>`

Deletes a job and its associated files.

- **Response**: Confirmation message indicating the job has been deleted.

- **Status Codes**:
    - `200 OK`: Job deleted successfully.
    - `404 Not Found`: Job ID does not exist.

#### DELETE `/api/v1/jobs/all` [DANGER!]

Deletes all jobs and their associated files. Use with caution as this will remove all job data including
the completed, queued, processing, and failed jobs.

- **Response**: Confirmation message indicating all jobs have been deleted.

- **Status Codes**:
    - `200 OK`: All jobs deleted successfully.

#### POST `/api/v1/jobs/triggerRemaining`

Triggers processing of any remaining jobs in the queue.

- **Response**: Confirmation message indicating remaining jobs have been triggered. You may get:
    - "Triggered processing for remaining queued jobs."
    - "Queue watcher is already running or not initialized."

- **Status Codes**:
    - `200 OK`: Remaining jobs triggered successfully.

#### POST `/api/v1/audio-duration`

Returns the duration (in seconds) of an uploaded audio file.

- **Request**: `multipart/form-data` with field `audioFile` (allowed: .mp3, .wav, .ogg)
- **Response**: `{ "duration": float }` (duration in seconds, rounded to 2 decimals)
- **Status Codes**:
    - `200 OK`: Duration returned successfully.
    - `400 Bad Request`: No file or invalid file type.
    - `500 Internal Server Error`: Could not determine duration.

#### POST `/api/v1/audio-size`

Returns the size of an uploaded audio file in human-readable format.

- **Request**: `multipart/form-data` with field `audioFile` (allowed: .mp3, .wav, .ogg)
- **Response**: `{ "size": string }` (e.g., "1.23 MB", "456 bytes")
- **Status Codes**:
    - `200 OK`: Size returned successfully.
    - `400 Bad Request`: No file or invalid file type.
    - `500 Internal Server Error`: Could not determine size.

#### POST `/api/v1/check-silence`

Checks if the uploaded audio file is silent.

- **Request**: `multipart/form-data` with field `audioFile` (allowed: .mp3, .wav, .ogg)
- **Response**: `{ "isSilent": bool }`
- **Status Codes**:
    - `200 OK`: Silence check returned successfully.
    - `400 Bad Request`: No file or invalid file type.
    - `500 Internal Server Error`: Error checking silence.

#### POST `/api/v1/normalize-audio`

Normalize an uploaded audio file and return a download link for the normalized file.

- **Request**: `multipart/form-data` with field `audioFile` (allowed: .mp3, .wav, .ogg)
    - Optional fields:
        - `normalizeBitrate`: Output bitrate (default: "256k")
        - `normalizeSampleRate`: Output sample rate (default: 44100)
        - `normalizeFilter`: Normalization filter ("loudnorm", "dynaudnorm", "volumedetect", "acompressor")
- **Response** (JSON): `{ "link": string, "filename": string }` (link to download normalized audio)
  ```json
  {
    "link": "/api/v1/download/normalized_audio.mp3",
    "filename": "normalized_audio.mp3"
  }
  ```
- **Status Codes**:
    - `200 OK`: Normalized audio link returned successfully.
    - `400 Bad Request`: No file or invalid file type.
    - `404 Not Found`: Could not find the generated file.
    - `500 Internal Server Error`: Error normalizing audio.

#### POST `/api/v1/generate-silent-audio`

Generate a silent audio file of a specified duration and format.

- **Request Body** (JSON):
    - `silentDuration`: Duration of the silent audio in seconds (float, required, >0).
    - `silentFormat`: Audio format for the silent file (e.g., ".wav", ".mp3", ".ogg").
- **Response** (JSON): `{ "link": string, "filename": string }` (link to download silent audio)
  ```json
  {
    "link": "/api/v1/download/silent_audio.mp3",
    "filename": "silent_audio.mp3"
  }
  ```
- **Status Codes**:
    - `200 OK`: Silent audio generated successfully.
    - `400 Bad Request`: Invalid input data (e.g., negative duration).
    - `404 Not Found`: Could not find the generated file.
    - `500 Internal Server Error`: Error generating silent audio.

</details>
</details>

## 🛠️ Preparation Steps

### Step 1: Install Whisper

```bash
pip install -U openai-whisper
```

To update to the latest version from the repository:

```bash
pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git
```

For more information on Whisper, refer to the [Whisper GitHub repository](ttps://github.com/openai/whisper)

### Step 2: Install FFmpeg

On Windows using Chocolatey (run as administrator in PowerShell):

```powershell
choco install ffmpeg
```

Or using Scoop (run as administrator in PowerShell):

```powershell
scoop install ffmpeg
```

### Step 3: Install Rust

```bash
pip install setuptools-rust
```

You may need to follow the Rust installation guide: https://www.rust-lang.org/learn/get-started

### Step 4: Install Kokoro TTS

```bash
pip install kokoro soundfile
```

For GPU acceleration, install PyTorch with CUDA support. Verify CUDA support with:

```python
import torch

# Should print True if CUDA is available.
print(torch.cuda.is_available())
```

### Step 5: Install Requirements

```bash
pip install -r requirements.txt
```

You can adjust the `torch` and `torchaudio` versions in `requirements.txt` to match your CUDA version.
For example, for CUDA 11.8:

```
--extra-index-url https://download.pytorch.org/whl/cu118
torch==2.7.1+cu118
torchaudio==2.7.1+cu118
```

You can also visit the official [PyTorch installation page](https://pytorch.org/get-started/locally/) to find the
correct command for your system.

### Step 6: Configure the Environment

1. Edit `configs.yaml` with your preferred settings:
    - Set `storePath` to your desired job storage location.
    - Configure `api.port` (default: 5000).
    - Adjust `tts.language` and `tts.voice` as needed.
    - Set appropriate Whisper model (`whisper.modelName`).
    - Configure video resolution and settings.

2. Add background videos to the directory specified by `video.default` (default: `./Assets/Videos`)
    - For horizontal videos, place them in `./Assets/Videos/Horizontal Videos`.
    - For vertical videos, place them in `./Assets/Videos/Vertical Videos`.
    - Ensure videos match the desired quality (e.g., 4K) and format.
    - You can get high-quality 4K videos from various sources like Pexels, Pixabay, or your own recordings.

3. Ensure all required directories exist (Optional; they exist by default):
    - `mkdir -p Jobs`
    - `mkdir -p Assets/Videos`
    - `mkdir -p Assets/Videos/Horizontal Videos`
    - `mkdir -p Assets/Videos/Vertical Videos`
    - `mkdir -p Assets/Audios`
    - `mkdir -p Assets/Fonts`

## 🚀 Usage Instructions

1. Start the server:

```bash
python Server.py
```

2. Submit text for video generation:

```bash
curl -X POST http://localhost:5000/api/v1/jobs \
     -F "text=This is a sample text to generate a video." \
     -F "language=en-us" \
     -F "voice=af_nova"
```

3. Monitor job status:

```bash
curl http://localhost:5000/api/v1/jobs/<returnedJobID>
```

4. Download the completed video:

```bash
curl http://localhost:5000/api/v1/jobs/<returnedJobID>/result --output Video.mp4
```

5. Delete a job and its files (to clean up and save space):

```bash
curl -X DELETE http://localhost:5000/api/v1/jobs/<returnedJobID>
```

## 🛠️ Troubleshooting

- If you encounter FFmpeg errors, verify FFmpeg is properly installed and in your PATH
- For TTS issues, check that Kokoro is properly installed and all dependencies are met
- If videos aren't generating correctly, verify background videos exist in the Assets directory
- Enable verbose logging in configs.yaml for detailed debugging information

## 💖 Support

If you want to support the development: https://coff.ee/hossammbalaha

## 📄 Copyright and License

> No part of this series may be reproduced, distributed, or transmitted in any form or by any means, including
> photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the
> author, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses
> permitted by copyright law. For permission requests, contact the author.

> The author is not responsible for any misuse of the code provided. The code is provided "as is" without warranty of
> any kind, either expressed or implied, including but not limited to the warranties of merchantability, fitness
> for a particular purpose, or non-infringement. In no event shall the author be liable for any claim, damages, or other
> liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the code
> or the use or other dealings in the code.

> If you need to use the code for research or commercial purposes, please contact the author for a written permission.

## 📬 Contact

For any questions or inquiries, please contact me using the contact information available on my CV at the following
link: https://hossambalaha.github.io/
