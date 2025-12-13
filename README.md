# 🎬 Audio-Captioned Automated Transcription & Video Generation Suite

[![Repo Size](https://img.shields.io/github/repo-size/HossamBalaha/Text2Video-Generation-Suite?style=flat-square)](https://github.com/HossamBalaha)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](#)
[![Status](https://img.shields.io/badge/status-Active-brightgreen?style=flat-square)](#)

A comprehensive, modular suite to automatically generate captioned videos from text or audio using Whisper, Kokoro TTS,
FFmpeg, and a Flask API. Includes 30 advanced audio processing tools for professional-grade media automation.

**Author:** Hossam Magdy Balaha  
**GitHub:** [https://github.com/HossamBalaha](https://github.com/HossamBalaha)  
**CV:** [hossambalaha.github.io](https://hossambalaha.github.io/)  
**Support:** [☕ Buy Me a Coffee](https://coff.ee/hossammbalaha)  
**Status:** Active Development

---

## 📑 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🚀 Quick Start (5 Minutes)](#-quick-start-5-minutes)
- [🎨 Web Interface](#-web-interface)
- [🤖 N8N Integration](#-n8n-integration--applicability)
- [🎵 Audio Tools (30 Tools)](#-audio-tools-comprehensive-suite)
- [📁 Project Structure](#-project-structure)
- [⚙️ Prerequisites](#️-prerequisites)
- [🛠️ Installation & Setup](#️-installation--setup)
- [🗣️ Supported TTS Voices & Languages](#️-supported-tts-voices--languages)
- [📺 Video Qualities & Resolutions](#-video-qualities--resolutions)
- [⚙️ Configuration Guide](#️-configuration-guide)
- [🚀 Batch Processing & Scaling](#-batch-processing--scaling)
- [💡 Performance Tips & Optimization](#-performance-tips--optimization)
- [📋 Real-World Examples & Workflows](#-real-world-examples--workflows)
- [🔧 Advanced Configuration](#-advanced-configuration)
- [🎯 Usage Instructions](#-usage-instructions)
- [🔌 API Reference](#-api-reference)
- [🐛 Troubleshooting](#-troubleshooting)
- [🧪 Testing & Validation](#-testing--validation)
- [🔐 Security Considerations](#-security-considerations)
- [🛠️ Development & Contribution](#️-development--contribution)
- [📖 Additional Resources](#-additional-resources)
- [📱 Deploying to Production](#-deploying-to-production)
- [📊 Monitoring & Logging](#-monitoring--logging)
- [📄 License & Attribution](#-license--attribution)
- [💬 Support & Community](#-support--community)
- [📞 Author & Contact](#-author--contact)
- [📈 Roadmap & Future Plans](#-roadmap--future-plans)
- [❓ FAQ](#-faq)
- [📊 Project Statistics](#-project-statistics)

---

## 🎯 Overview

This is a complete end-to-end solution for automated, AI-driven video content creation. It transforms text or audio
input into professional-quality, caption-synchronized videos suitable for social media, education, marketing, and
automation platforms like N8N.

**Core Workflow:**

1. Submit text or audio via API, web UI, or automated workflow
2. System transcribes audio or generates voiceover from text
3. Extract timing information for precise caption synchronization
4. Select background video assets and generate final captioned video
5. Process with advanced audio tools for professional quality
6. Download or integrate into automated publishing pipelines

**Ideal For:**

- Content creators generating shorts/reels
- Educational content automation
- Marketing teams producing videos at scale
- N8N automation workflows
- Custom video pipeline development

---

## ✨ Key Features

### Video Generation

- **End-to-End Automation:** Transform text/audio into synchronized, captioned videos with natural-sounding voiceovers
- **Speech & Transcription:** Whisper for accurate speech-to-text with word-level timing and multilingual support
- **Text-to-Speech:** Kokoro TTS with multiple languages, voices, and customizable speech rates
- **Advanced Video Processing:** FFmpeg for trimming, merging, format conversion, and caption overlay

### Audio Processing Suite (30 Tools)

- **Analysis:** Duration, size, silence detection, audio analysis
- **Enhancement:** Noise reduction, silence removal, bass/treble boost, compression, stereo adjustment
- **Transformation:** Channel conversion, pitch shifting, looping, echo effects, crossfading
- **Generation:** Waveform visualization, spectrum analysis, speech-to-text transcription
- **Advanced:** Multi-track mixing, audio merging, format conversion, trim/split operations

### Platform Features

- **RESTful API:** Robust Flask API with comprehensive endpoint coverage
- **Web Interface:** Modern, responsive UI for job submission and tool access
- **Flexible I/O:** MP3, WAV, OGG audio; 4K, Full HD video quality; horizontal/vertical formats
- **Batch Processing:** Submit multiple jobs for scalable automation
- **Extensible Design:** Modular architecture for easy integration and customization
- **N8N Ready:** Seamless integration with N8N workflow automation

---

## 🚀 Quick Start (5 Minutes)

### 1. Install & Run

```bash
# Clone and setup
git clone https://github.com/HossamBalaha/Text2Video-Generation-Suite.git
cd Text2Video-Generation-Suite

# Install dependencies
pip install -r requirements.txt

# Run server
python Server.py
```

### 2. Access the App

Open `http://localhost:5000` in your browser

### 3. Generate Your First Video

1. Go to **Text to Video** tab
2. Enter text: *"Hello world, this is my first generated video"*
3. Select language: **English**
4. Select voice: **af_nova**
5. Click **Create Job**
6. Monitor in **Jobs** tab
7. Download when complete ✅

---

## 🎨 Web Interface

Modern, user-friendly interface built with Flask and Bootstrap for seamless interaction.

**Key Technologies:**

- Flask (Python web framework)
- Bootstrap 5 (responsive design)
- jQuery & vanilla JavaScript
- HTML5 & CSS3

**Pages & Features:**

### 📑 Index

Overview page with quick access to main features and project introduction.

### 📝 Text to Video

Generate videos from text input with customizable:

- Language and voice selection
- Video type (horizontal/vertical)
- Quality settings (4K, Full HD, etc.)
- Real-time job submission and tracking

### 📊 T2V Jobs Management

Track and manage all video generation jobs:

- Real-time status updates
- Job details and progress
- Download final videos
- Job history

### 🎵 Audio Tools

Access all 30 audio processing tools:

- Interactive tool cards with descriptions
- Modal dialogs with form inputs
- Real-time processing with status indicators
- Automatic download on completion

---

## 🤖 N8N Integration & Applicability

Seamlessly integrate with N8N workflow automation for powerful media production orchestration:

### Automation Capabilities

- **Auto-Trigger:** Start video creation from emails, webhooks, cloud uploads, or database records
- **Batch Processing:** Schedule or batch-submit multiple jobs for large-scale production
- **Multi-Step Workflows:** Chain transcription → TTS → video assembly → publishing
- **API Integration:** HTTP Request nodes interact with all REST endpoints
- **Conditional Logic:** Route jobs based on status, retry failed tasks, send notifications
- **Content Enrichment:** Combine with N8N nodes for scripts, translation, branding
- **Scalable Automation:** Connect with cloud storage, databases, and third-party services

### Example N8N Workflow

```
Webhook Trigger
    ↓
Submit Job → /api/v1/jobs
    ↓
Poll Status → /api/v1/jobs/<jobId>
    ↓
Download → /api/v1/jobs/<jobId>/result
    ↓
Publish → YouTube/TikTok/Drive
    ↓
Notify → Slack/Email
```

### Benefits

- No-code automation for non-developers
- Visual workflow builder
- Hundreds of service integrations
- Scalable, repeatable media production

See [N8N Documentation](https://n8n.io/docs/) for integration details.

---

## 🎵 Audio Tools: Comprehensive Suite

### 30 Total Audio Tools

**15 Pre-existing Tools:**

- Get Audio Duration
- Get Audio Size
- Check Silence
- Normalize Audio
- Generate Silent Audio
- Convert Audio
- Change Volume
- Change Speed
- Reverse Audio
- Extract Audio
- Concatenate Audios
- Split Audio
- Fade In/Out
- Remove Vocals
- Equalizer/Filter

**15 New Tools (December 2025):**

#### Analysis & Measurement (4)

- **🎵 Get Audio Duration** - Extract audio length in seconds
- **📊 Get Audio Size** - Check file size in various units
- **🔍 Check Silence** - Detect if audio is silent
- **📈 Analyze Audio** - Get comprehensive metrics (codec, bitrate, sample rate, channels)

#### Enhancement & Processing (5)

- **🔊 Reduce Noise** - Remove background noise using FFmpeg denoiser
- **🔇 Remove Silence** - Automatically delete silent portions
- **🎚️ Enhance Audio** - Boost bass and treble (-20 to +20 dB)
- **📉 Compress Audio** - Apply dynamic range compression with configurable parameters
- **🎧 Adjust Stereo Width** - Control stereo field width (0=mono, 1=normal, 2=wide)

#### Conversion & Transformation (3)

- **🔄 Convert Channels** - Stereo ↔ Mono conversion
- **🎼 Shift Pitch** - Change pitch without affecting speed (±12 semitones)
- **🔁 Loop Audio** - Create seamless audio loops with specified duration

#### Effects & Blending (2)

- **🎵 Add Echo** - Add echo/delay effects (configurable delay and decay)
- **🔀 Crossfade Audio** - Create smooth transitions between two tracks

#### Generation & Visualization (3)

- **📊 Generate Waveform** - Create visual waveform PNG image
- **🎨 Generate Spectrum** - Create spectrum analyzer video visualization
- **🎤 Transcribe Audio** - Convert speech to text (TXT/JSON/SRT formats)

#### Advanced Operations (1)

- **🎵 Mix Audio** - Combine multiple audio tracks simultaneously with volume control

### API Endpoints (30 Total)

#### Audio Analysis

```
POST /api/v1/audio-duration          - Get duration
POST /api/v1/audio-size              - Get file size
POST /api/v1/check-silence           - Detect silence
POST /api/v1/analyze-audio           - Comprehensive analysis
```

#### Audio Processing

```
POST /api/v1/reduce-noise            - Noise reduction
POST /api/v1/remove-silence          - Remove silent portions
POST /api/v1/enhance-audio           - Bass/treble enhancement
POST /api/v1/compress-audio          - Dynamic compression
POST /api/v1/convert-channels        - Channel conversion
POST /api/v1/loop-audio              - Audio looping
POST /api/v1/shift-pitch             - Pitch shifting
POST /api/v1/add-echo                - Echo effects
POST /api/v1/adjust-stereo           - Stereo width adjustment
POST /api/v1/generate-waveform       - Waveform generation
POST /api/v1/generate-spectrum       - Spectrum visualization
POST /api/v1/crossfade-audio         - Audio crossfading
POST /api/v1/transcribe-audio        - Speech-to-text
POST /api/v1/mix-audio               - Multi-track mixing
```

#### Existing Tools

```
POST /api/v1/normalize-audio         - Audio normalization
POST /api/v1/generate-silent-audio   - Generate silence
POST /api/v1/convert-audio           - Format conversion
POST /api/v1/change-volume           - Volume adjustment
POST /api/v1/change-speed            - Speed adjustment
POST /api/v1/reverse-audio           - Reverse audio
POST /api/v1/extract-audio           - Extract from video
POST /api/v1/concat-audio            - Concatenate files
POST /api/v1/split-audio             - Split into segments
POST /api/v1/fade-audio              - Fade in/out
POST /api/v1/remove-vocals           - Vocal removal
POST /api/v1/equalize-audio          - EQ filtering
```

#### File Management

```
GET /api/v1/download/<filename>      - Download processed files
```

---

## 📁 Project Structure

```
Text2Video-Generation-Suite/
├── README.md                      # This file
├── configs.yaml                   # Main configuration file
├── requirements.txt               # Python dependencies
├── Server.py                      # API server with all endpoints
├── ConfigsSettings.py             # Configuration parser
├── FFMPEGHelper.py                # FFmpeg wrapper (audio/video processing)
├── TextToSpeechHelper.py          # Kokoro TTS integration
├── WhisperTranscribeHelper.py     # Whisper transcription
├── VideoCreatorHelper.py          # Video assembly logic
├── TextHelper.py                  # Text processing utilities
├── routes.py                      # Web UI routes
├── apiRoutes.py                   # API endpoint definitions
│
├── Jobs/                          # Job storage directory
│   ├── <jobId>/
│   │   ├── job.json               # Job metadata
│   │   ├── audio.mp3              # Generated audio
│   │   └── <jobId>_Final.mp4      # Final video output
│
├── Assets/                        # Static assets
│   ├── Videos/
│   │   ├── Horizontal Videos/     # Horizontal format backgrounds
│   │   └── Vertical Videos/       # Vertical format backgrounds
│   ├── Audios/                    # Test audio files
│   └── Fonts/                     # Caption fonts
│
├── templates/                     # HTML templates
│   ├── base.html                  # Base template
│   ├── index.html                 # Homepage
│   ├── text2Video.html            # Video generation page
│   ├── audioTools.html            # Audio tools page
│   └── jobs.html                  # Job management page
│
├── static/                        # Static files
│   ├── css/
│   │   └── styles.css             # Main stylesheet
│   ├── js/
│   │   └── scripts.js             # Interactive scripts
│   └── images/                    # UI images and logos
│
└── tests/                         # Test suites
    ├── TestAudioTools.py          # Audio tools test suite
    └── TestAudioEndpoints.py      # API endpoint tests
```

### Core Configuration (configs.yaml)

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

audio:
  allowedExtensions: [ ".mp3", ".wav", ".ogg" ]
  default: "./Assets/Audios"
```

---

## ⚙️ Prerequisites

- **Python 3.10+**
- **FFmpeg** with audio/video codec support
- **pip** (Python package manager)
- **Git** (optional, for cloning)
- **4GB+ RAM** (recommended for TTS/Whisper models)
- **10GB+ Disk Space** (for models and job storage)

---

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/HossamBalaha/Text2Video-Generation-Suite.git
cd Text2Video-Generation-Suite
```

### 2. Verify FFmpeg Installation

```bash
# Windows
ffmpeg -version
ffprobe -version

# Linux/Mac
which ffmpeg
which ffprobe
```

If not installed:

```bash
# Windows (with chocolatey)
choco install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS (with homebrew)
brew install ffmpeg
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**

- Flask - Web framework
- ffmpeg-python - FFmpeg wrapper
- openai-whisper - Speech-to-text
- torch - Deep learning framework
- requests - HTTP library

### 4. Verify Configuration

```bash
# Review default settings
cat configs.yaml

# Optionally edit for your needs
# All settings can be adjusted in ConfigsSettings.py
```

### 5. Prepare Assets

```bash
# Add background videos
# Place video files in: Assets/Videos/Horizontal Videos/ or Vertical Videos/

# Add test audio files (optional)
# Place in: Assets/Audios/

# Add custom fonts (optional)
# Place in: Assets/Fonts/
```

### 6. Run Server

```bash
python Server.py
```

Server will start at: `http://localhost:5000`

---

## 🚀 Quick Start (5 Minutes)

### 1. Install & Run

```bash
# Clone and setup
git clone https://github.com/HossamBalaha/Text2Video-Generation-Suite.git
cd Text2Video-Generation-Suite

# Install dependencies
pip install -r requirements.txt

# Run server
python Server.py
```

### 2. Access the App

Open `http://localhost:5000` in your browser

### 3. Generate Your First Video

1. Go to **Text to Video** tab
2. Enter text: *"Hello world, this is my first generated video"*
3. Select language: **English**
4. Select voice: **af_nova**
5. Click **Create Job**
6. Monitor in **Jobs** tab
7. Download when complete ✅

---

## 🎯 Usage Instructions

### Via Web Interface

1. **Navigate to UI:**
    - Home: `http://localhost:5000/`
    - Video Generation: `http://localhost:5000/text2Video`
    - Audio Tools: `http://localhost:5000/audioTools`
    - Job Management: `http://localhost:5000/jobs`

2. **Generate Video:**
    - Enter text for conversion (max 6500 characters)
    - Select language, voice, quality, type
    - Submit job
    - Monitor status in real-time
    - Download when complete

3. **Use Audio Tools:**
    - Click desired tool card
    - Upload audio file(s)
    - Configure parameters as needed
    - Process
    - Automatically download result

4. **Manage Jobs:**
    - View all jobs with status
    - See job creation timestamps
    - Download completed videos
    - Track processing progress

### Via REST API

#### Create Video Job

```bash
curl -X POST http://localhost:5000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text here",
    "language": "en-us",
    "voice": "af_nova",
    "videoType": "Horizontal",
    "videoQuality": "4K"
  }'
```

#### Check Job Status

```bash
curl http://localhost:5000/api/v1/jobs/<jobId>
```

#### Download Result

```bash
curl -O http://localhost:5000/api/v1/jobs/<jobId>/result
```

#### Use Audio Tools

```bash
# Example: Reduce Noise
curl -X POST http://localhost:5000/api/v1/reduce-noise \
  -F "audioFile=@input.mp3" \
  -F "noiseReduction=20"

# Example: Mix Audio
curl -X POST http://localhost:5000/api/v1/mix-audio \
  -F "audioFiles=@audio1.mp3" \
  -F "audioFiles=@audio2.mp3" \
  -F "volumes=1.0,0.8"

# Example: Transcribe
curl -X POST http://localhost:5000/api/v1/transcribe-audio \
  -F "audioFile=@voice.mp3" \
  -F "language=en" \
  -F "outputFormat=txt"
```

---

## 🔌 API Reference

### Video Generation API

#### POST `/api/v1/jobs`

Submit a new video generation job.

**Request:**

```json
{
  "text": "Your text content",
  "language": "en-us",
  "voice": "af_nova",
  "speechRate": 1.0,
  "videoType": "Horizontal",
  "videoQuality": "4K"
}
```

**Response (202 Accepted):**

```json
{
  "jobId": "abc123def456..."
}
```

#### GET `/api/v1/jobs/<jobId>`

Get job status and metadata.

**Response (200 OK):**

```json
{
  "jobId": "abc123def456...",
  "status": "completed",
  "text": "Your text...",
  "language": "en-us",
  "voice": "af_nova",
  "videoType": "Horizontal",
  "videoQuality": "4K",
  "createdAt": "2025-12-10 10:30:00"
}
```

#### GET `/api/v1/jobs/<jobId>/result`

Download the final video file.

**Response:** Video file (binary)

#### DELETE `/api/v1/jobs/<jobId>`

Delete a job and associated files.

#### GET `/api/v1/languages`

Get available TTS languages.

#### GET `/api/v1/voices`

Get available TTS voices.

#### GET `/api/v1/videoTypes`

Get available video types (Horizontal, Vertical).

#### GET `/api/v1/videoQualities`

Get available video qualities (4K, Full HD, etc.).

### Audio Tools API

All audio tool endpoints follow this pattern:

**Request:** POST `/api/v1/<tool-name>`

```
multipart/form-data with:
- audioFile: Audio file upload
- Other parameters: Tool-specific settings
```

**Response (200 OK):**

```json
{
  "link": "/api/v1/download/filename.ext",
  "filename": "filename.ext"
}
```

**Error Response (400/500):**

```json
{
  "error": "Error description"
}
```

---

## 🧪 Testing

### Run Test Suite

```bash
# Test all audio tools
python tests/TestAudioTools.py

# Run specific tests
python -m pytest tests/TestAudioTools.py::AudioToolsTester::test_reduce_noise
```

### Manual Testing Checklist

- [ ] Video generation from text
- [ ] Audio file upload and processing
- [ ] Job status tracking
- [ ] File downloads
- [ ] Error handling
- [ ] API endpoint responses
- [ ] UI responsiveness
- [ ] Large file handling

---

## 🗣️ Supported TTS Voices & Languages

### Available Languages

| Language | Code | Example Voice |
|----------|------|----------------|
| English (US) | `en-us` | af_nova |
| English (UK) | `en-gb` | bf_emma |
| Spanish | `es-es` | e_diosa |
| French | `fr-fr` | f_ailette |
| German | `de-de` | d_barbora |
| Japanese | `ja-jp` | j_michiko |
| Chinese (Mandarin) | `zh-cn` | z_zoe |
| Portuguese (Brazilian) | `pt-br` | p_ana |

### Popular Voices

**English (US) - `en-us`:**
- `af_nova` - Professional, neutral
- `af_bella` - Warm, friendly
- `af_sarah` - Clear, articulate
- `am_michael` - Deep, authoritative
- `am_adam` - Casual, conversational

Get full voice list via API:
```bash
curl http://localhost:5000/api/v1/voices
```

---

## 📺 Video Qualities & Resolutions

### Supported Resolutions

| Quality | Resolution | Bitrate | Aspect Ratio | Use Case |
|---------|-----------|---------|--------------|----------|
| **4K** | 3840×2160 | 5000k | 16:9 (H) / 9:16 (V) | Premium, archival |
| **Full HD** | 1920×1080 | 4000k | 16:9 (H) / 9:16 (V) | YouTube, streaming |
| **HD** | 1280×720 | 3000k | 16:9 (H) / 9:16 (V) | Web, mobile |
| **480p** | 854×480 | 2000k | 16:9 (H) / 9:16 (V) | Mobile, low bandwidth |
| **360p** | 640×360 | 1500k | 16:9 (H) / 9:16 (V) | Preview, thumbnail |

### Aspect Ratios

- **Horizontal (16:9):** YouTube, Vimeo, Facebook, Twitch
- **Vertical (9:16):** TikTok, Instagram Reels, YouTube Shorts, Snapchat

---

## ⚙️ Configuration Guide

### Environment Variables

Set configuration via environment variables (overrides configs.yaml):

```bash
# Server Configuration
export API_PORT=5000
export API_MAX_JOBS=1
export API_MAX_TEXT_LENGTH=6500
export API_TIMEOUT=10

# TTS Configuration
export TTS_LANGUAGE=en-us
export TTS_VOICE=af_nova
export TTS_SPEECH_RATE=1.0

# Whisper Configuration
export WHISPER_MODEL=turbo
export WHISPER_LANGUAGE=en

# Video Configuration
export VIDEO_TYPE=Horizontal
export VIDEO_QUALITY=4K

# Logging
export VERBOSE=true
```

### Modifying configs.yaml

Edit `configs.yaml` directly for persistent configuration:

```yaml
api:
  maxJobs: 2              # Process 2 videos simultaneously
  maxTextLength: 10000    # Allow longer text input
  port: 8000              # Run on different port
  
tts:
  voice: "af_bella"       # Default voice
  speechRate: 0.9         # Slower speech

ffmpeg:
  videoBitrate: "8000k"   # Higher quality
  audioCodec: "libvorbis" # Different codec
```

After modifying, restart the server:
```bash
python Server.py
```

---

## 🚀 Batch Processing & Scaling

### Submit Multiple Jobs

```python
import requests
import json

# Submit 5 jobs
for i in range(5):
    response = requests.post(
        'http://localhost:5000/api/v1/jobs',
        json={
            'text': f'Video number {i+1}',
            'language': 'en-us',
            'voice': 'af_nova',
            'videoType': 'Horizontal',
            'videoQuality': '4K'
        }
    )
    job_id = response.json()['jobId']
    print(f'Job {i+1} submitted: {job_id}')
```

### Check All Jobs Status

```bash
# Get job history
curl http://localhost:5000/api/v1/jobs

# Poll specific job
curl http://localhost:5000/api/v1/jobs/<jobId>
```

### Configuration for Batch Processing

```yaml
# In configs.yaml for production scaling
api:
  maxJobs: 4              # Process 4 videos in parallel
  maxTimeout: 120         # Allow 2 minutes per job
```

---

## 💡 Performance Tips & Optimization

### Memory Optimization

```python
# Reduce model size in whisper
# Use "base" instead of "turbo" for faster processing
configs['whisper']['modelName'] = 'base'

# Reduce video quality for faster encoding
videoQuality = 'HD'  # Instead of '4K'
```

### Speed Optimization

```yaml
# In configs.yaml
ffmpeg:
  videoBitrate: "2000k"   # Lower bitrate = faster encoding
  fps: 24                 # 24fps instead of 30fps
  videoCodec: "libx265"   # H.265 codec (slower encoding, better quality)

whisper:
  modelName: "base"       # Smaller model = faster
```

### Quality Optimization

```yaml
ffmpeg:
  videoBitrate: "8000k"   # Higher bitrate = better quality
  audioCodec: "libvorbis" # Better audio codec
  pixelFormat: "yuv444p"  # Better color depth
```

### For Long Content

- Split text into multiple jobs (one video per paragraph)
- Use lower quality initially, re-encode with higher quality later
- Process during off-peak hours if possible

---

## 📋 Real-World Examples & Workflows

### Example 1: YouTube Short Generator

```bash
# Generate 10 educational shorts automatically
for i in {1..10}; do
  TEXT="Learning concept $i: This is an educational video about topic $i"
  curl -X POST http://localhost:5000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"$TEXT\",
      \"language\": \"en-us\",
      \"voice\": \"af_nova\",
      \"videoType\": \"Vertical\",
      \"videoQuality\": \"Full HD\"
    }"
done
```

### Example 2: Podcast Video Generation

```python
# Convert podcast transcript to video
podcast_text = """
In today's episode, we discuss the future of AI.
Artificial intelligence is transforming industries.
[Full podcast transcript here...]
"""

response = requests.post(
    'http://localhost:5000/api/v1/jobs',
    json={
        'text': podcast_text,
        'language': 'en-us',
        'voice': 'am_michael',  # Deep voice for authority
        'videoType': 'Horizontal',
        'videoQuality': 'Full HD',
        'speechRate': 0.9  # Slightly slower
    }
)
```

### Example 3: Audio Processing Pipeline

```bash
# Enhance podcast audio
curl -X POST http://localhost:5000/api/v1/reduce-noise \
  -F "audioFile=@podcast.mp3" \
  -F "noiseReduction=25"

# Then compress for web
curl -X POST http://localhost:5000/api/v1/compress-audio \
  -F "audioFile=@denoised.mp3" \
  -F "threshold=-20" \
  -F "ratio=4"

# Generate waveform visualization
curl -X POST http://localhost:5000/api/v1/generate-waveform \
  -F "audioFile=@compressed.mp3" \
  --output waveform.png
```

### Example 4: Multi-Language Content

```python
languages = ['en-us', 'es-es', 'fr-fr', 'de-de']
text = "Welcome to our global product launch"

for lang in languages:
    requests.post(
        'http://localhost:5000/api/v1/jobs',
        json={
            'text': text,
            'language': lang,
            'videoType': 'Horizontal',
            'videoQuality': '4K'
        }
    )
```

---

## 🔧 Advanced Configuration

### Custom FFmpeg Filters

Modify `configs.yaml` to use custom FFmpeg filters:

```yaml
ffmpeg:
  # Custom audio normalization
  normalizationFilter: "loudnorm=I=-16:TP=-1.5:LRA=11"
  
  # Custom caption styling
  captionFont: "./Assets/Fonts/CustomFont/font.ttf"
  captionTextBorderWidth: 3
  captionTextColor: "yellow"
  
  # Advanced video codec settings
  videoBitrate: "8000k"
  videoCodec: "libx265"  # H.265 for better compression
```

### Custom Background Videos

```bash
# Add your background videos
cp your_video.mp4 Assets/Videos/Horizontal\ Videos/
cp vertical_video.mp4 Assets/Videos/Vertical\ Videos/

# Restart server
python Server.py
```

The system will automatically use available videos for video generation.

---

## 🐛 Troubleshooting

### FFmpeg Not Found

```bash
# Verify installation
ffmpeg -version

# Add to PATH if needed
# Windows: Set environment variables
# Linux/Mac: Check installation location
```

### Out of Memory

- Reduce video quality to 'HD' or '480p'
- Process smaller files
- Increase available RAM or enable virtual memory
- Check system resources: `free -h` (Linux) or Task Manager (Windows)
- Reduce `maxJobs` in configuration

### Timeout Errors

- Increase `maxTimeout` in configs.yaml
- Use smaller text input (max 6500 chars)
- Check server CPU/memory usage
- Try with lower video quality

### File Not Found Errors

- Verify file paths exist
- Check file permissions: `chmod 644 filename`
- Ensure Assets directory structure: `Assets/Videos/Horizontal Videos/` and `Assets/Videos/Vertical Videos/`
- Confirm file extensions are supported

### API Connection Issues

- Verify server is running: `python Server.py`
- Check port 5000 is available: `netstat -an | grep 5000` (Linux/Mac) or `netstat -ano | findstr :5000` (Windows)
- Confirm network connectivity
- Review firewall settings
- Check localhost vs 0.0.0.0 binding

### Audio Quality Issues

- Check source file quality and format
- Review FFmpeg compression settings
- Verify TTS voice selection and speech rate
- Inspect FFmpeg parameters in configs.yaml
- Try different audio codec (libvorbis, aac, etc.)

### Job Stays in 'Queued' State

- Check `maxJobs` setting (default is 1, process sequentially)
- Verify server is actually processing: check console output
- Restart server: `python Server.py`
- Check disk space availability

### Video Generation Fails

- Verify background videos exist in Assets/Videos/
- Check if text is too long (max 6500 characters)
- Confirm TTS voice is valid
- Try with simpler text first
- Check FFmpeg installation and dependencies

### UI Not Loading

- Verify Flask server started successfully
- Check if port 5000 is in use
- Clear browser cache (Ctrl+Shift+Delete)
- Try different browser
- Check browser console for JavaScript errors

---

## 📱 Deploying to Production

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy files
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p Assets/Videos Assets/Audios Assets/Fonts Jobs

# Expose port
EXPOSE 5000

# Run server
CMD ["python", "Server.py"]
```

Build and run:

```bash
docker build -t text2video:latest .
docker run -p 5000:5000 -v $(pwd)/Jobs:/app/Jobs text2video:latest
```

### Cloud Deployment

**Heroku:**
```bash
heroku create your-app-name
git push heroku main
heroku config:set API_PORT=5000
```

**AWS/Google Cloud/Azure:**
- Use Docker container from above
- Set environment variables in cloud console
- Mount persistent volume for Jobs directory
- Scale horizontally with load balancer

### Using Gunicorn for Production

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 Server:app
```

---

## 📊 Monitoring & Logging

### Enable Detailed Logging

```bash
# Set verbose mode
export VERBOSE=true
python Server.py
```

### Monitor Job Processing

```bash
# Check active jobs
curl http://localhost:5000/api/v1/ready

# Get job status
curl http://localhost:5000/api/v1/jobs/<jobId>

# Check server health
curl http://localhost:5000/api/v1/status
```

### View System Resources

```bash
# Linux/Mac
top                    # CPU and memory
df -h                  # Disk space
du -sh Jobs/           # Jobs directory size

# Windows
tasklist              # Running processes
systeminfo            # System info
dir /s Jobs\          # Directory size
```

---

## 📖 Additional Resources

For more detailed information, refer to these documentation files:

- **AUDIO_TOOLS_QUICK_REFERENCE.md** - API endpoints and code examples
- **AUDIO_TOOLS_IMPLEMENTATION.md** - Technical implementation details
- **IMPLEMENTATION_SUMMARY.md** - Project overview and deployment
- **COMPLETION_CHECKLIST.md** - Verification and testing results
- **PROJECT_FINAL_REPORT.md** - Formal project report
- **DOCUMENTATION_INDEX.md** - Complete documentation navigation

---

## 🧪 Testing & Validation

### Automated Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python tests/TestAudioTools.py

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Manual Testing Checklist

- [ ] Server starts without errors
- [ ] Web UI loads at localhost:5000
- [ ] Can submit text-to-video job
- [ ] Job status updates in real-time
- [ ] Video generation completes successfully
- [ ] Downloaded video plays correctly
- [ ] Audio tools accept file uploads
- [ ] Audio tools process files correctly
- [ ] API endpoints return proper responses
- [ ] Error handling works as expected
- [ ] File downloads work correctly
- [ ] Large files are handled properly

### Load Testing

```python
import concurrent.futures
import requests
import time

def submit_job():
    response = requests.post(
        'http://localhost:5000/api/v1/jobs',
        json={
            'text': 'Test video',
            'language': 'en-us',
            'voice': 'af_nova',
            'videoType': 'Horizontal',
            'videoQuality': 'HD'
        }
    )
    return response.json()

# Submit 10 jobs concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(submit_job) for _ in range(10)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    print(f'Submitted {len(results)} jobs')
```

---

## 🔐 Security Considerations

### Input Validation

The application validates:
- Text length (max 6500 characters)
- File upload sizes
- File extensions (audio: .mp3, .wav, .ogg, .flac)
- Language and voice parameters

### Running Behind a Proxy

For production, use a reverse proxy (nginx, Apache):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Rate Limiting (Manual Implementation)

To add rate limiting, modify `apiRoutes.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

---

## 🛠️ Development & Contribution

### Project Structure for Developers

```
Text2Video-Generation-Suite/
├── Server.py                    # Main entry point
├── apiRoutes.py                 # REST API routes
├── routes.py                    # Web UI routes
│
├── Helpers/
│   ├── VideoCreatorHelper.py   # Video assembly
│   ├── TextToSpeechHelper.py   # TTS integration
│   ├── WhisperTranscribeHelper.py # Speech-to-text
│   ├── FFMPEGHelper.py         # Media processing
│   ├── TextHelper.py           # Text utilities
│   └── WebHelpers.py           # Web utilities
│
├── Config/
│   ├── configs.yaml            # Configuration file
│   └── ConfigsSettings.py      # Config parser
│
├── Assets/
│   ├── Videos/                 # Background videos
│   ├── Audios/                 # Test audio files
│   └── Fonts/                  # Caption fonts
│
└── tests/                       # Test suites
```

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/HossamBalaha/Text2Video-Generation-Suite.git
cd Text2Video-Generation-Suite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/ -v

# Code formatting
black . --line-length=100

# Linting
flake8 .
```

### Adding New Audio Tools

1. Implement in `FFMPEGHelper.py`:
```python
def MyNewTool(self, audioFile, parameter1, parameter2):
    """
    Description of the tool.
    
    Args:
        audioFile: Path to audio file
        parameter1: First parameter
        parameter2: Second parameter
    
    Returns:
        Path to output file
    """
    # Implementation here
    pass
```

2. Add API endpoint in `apiRoutes.py`:
```python
@apiBp.route("/api/v1/my-new-tool", methods=["POST"])
def MyNewTool():
    # Handle request
    pass
```

3. Add web UI card in `templates/audioTools.html`

4. Add test in `tests/TestAudioTools.py`

### Contributing Guidelines

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/my-feature`
3. **Make your changes and commit:** `git commit -m "Add my feature"`
4. **Push to the branch:** `git push origin feature/my-feature`
5. **Submit a pull request**

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions
- Keep functions under 50 lines
- Write meaningful commit messages

---

## 📄 License & Attribution

### License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) file for full details.

**Summary:**
- ✅ Free to use, modify, and distribute
- ✅ No warranty provided
- ✅ Attribution appreciated but not required
- ✅ Can be used in commercial projects

### Citation

If you use this project in academic work or publications, please cite:

```bibtex
@software{balaha2025text2video,
  author = {Hossam Magdy Balaha},
  title = {Audio-Captioned Automated Transcription & Video Generation Suite},
  year = {2025},
  url = {https://github.com/HossamBalaha/Text2Video-Generation-Suite},
  version = {2.0.0}
}
```

Or in APA format:

```
Balaha, H. M. (2025). Audio-Captioned Automated Transcription & Video Generation Suite (v2.0.0). 
Retrieved from https://github.com/HossamBalaha/Text2Video-Generation-Suite
```

### Third-Party Libraries

This project uses and acknowledges:

| Library | Purpose | License |
|---------|---------|---------|
| **OpenAI Whisper** | Speech-to-text transcription | MIT |
| **Kokoro TTS** | Text-to-speech synthesis | Apache 2.0 |
| **FFmpeg** | Multimedia processing | LGPL/GPL |
| **Flask** | Web framework | BSD |
| **PyTorch** | Deep learning | BSD |
| **Pillow** | Image processing | HPND |
| **NumPy** | Numerical computing | BSD |

---

## 💬 Support & Community

### Getting Help

**Documentation:**
- 📖 [README.md](README.md) - Complete project documentation
- 📋 [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Documentation navigation

**Communication:**
- 🐛 [GitHub Issues](https://github.com/HossamBalaha/Text2Video-Generation-Suite/issues) - Report bugs
- 💡 [GitHub Discussions](https://github.com/HossamBalaha/Text2Video-Generation-Suite/discussions) - Ask questions
- 📧 Contact via GitHub profile

### Support the Project

If you find this project helpful:

- ⭐ **Star the repository** on GitHub
- 🔄 **Share with others** who might benefit
- 🐛 **Report bugs** and suggest improvements
- 🤝 **Contribute code** via pull requests
- ☕ **Support the author:** [Buy Me a Coffee](https://coff.ee/hossammbalaha)

### Community Guidelines

- Be respectful and constructive
- Search existing issues before creating new ones
- Provide detailed information when reporting bugs
- Follow the code of conduct

---

## 📞 Author & Contact

**Hossam Magdy Balaha**

| Platform | Link |
|----------|------|
| **GitHub** | [HossamBalaha](https://github.com/HossamBalaha) |
| **Portfolio** | [hossambalaha.github.io](https://hossambalaha.github.io/) |
| **Support** | [☕ Buy Me a Coffee](https://coff.ee/hossammbalaha) |

**Project Repository:**
- [Text2Video-Generation-Suite](https://github.com/HossamBalaha/Text2Video-Generation-Suite)

---

## 🙏 Acknowledgments

Special thanks to:

- **OpenAI** for the Whisper API - making accurate speech-to-text accessible
- **Kokoro TTS** - providing high-quality text-to-speech synthesis
- **FFmpeg** - the backbone of multimedia processing
- **Flask** - enabling fast, lightweight web development
- **PyTorch** - powering deep learning capabilities
- **N8N** - making workflow automation accessible
- **All contributors** who have helped improve this project

---

## 📈 Roadmap & Future Plans

### Current Version (2.0.0)
- ✅ 30 audio processing tools
- ✅ Text-to-video generation with captions
- ✅ REST API with comprehensive endpoints
- ✅ Web UI with job management
- ✅ N8N integration support

### Planned Features (Q1 2026)
- 🔲 Batch processing with queue management
- 🔲 GPU acceleration support
- 🔲 Multi-GPU support
- 🔲 Advanced scheduling and automation
- 🔲 Database integration for job persistence
- 🔲 User authentication and management
- 🔲 Webhook notifications
- 🔲 Video subtitle overlays with styling
- 🔲 Music generation integration
- 🔲 Custom model fine-tuning

### Planned Features (Q2-Q3 2026)
- 🔲 Mobile app (iOS/Android)
- 🔲 Desktop app (Windows/Mac/Linux)
- 🔲 Collaboration features
- 🔲 Advanced analytics and reporting
- 🔲 Plugin/extension system

---

## ❓ FAQ

### Q: Can I use this commercially?
**A:** Yes! The MIT license allows commercial use. Attribution is appreciated but not required.

### Q: What's the maximum text length?
**A:** Default is 6500 characters, configurable in `configs.yaml`. Longer text will take more time to process.

### Q: Can I customize the TTS voices?
**A:** You can choose from available Kokoro voices. Custom fine-tuning is possible but requires additional setup.

### Q: Does it support multiple languages?
**A:** Yes! It supports 8+ languages via Kokoro TTS and Whisper for transcription.

### Q: Can I run this on Windows/Mac?
**A:** Yes! Python 3.10+ and FFmpeg work on all major operating systems.

### Q: How long does video generation take?
**A:** Typically 2-10 minutes depending on:
- Text length (30 seconds = ~1 minute processing)
- Video quality (4K slower than HD)
- System specs (CPU/GPU)
- Current server load

### Q: Can I use my own background videos?
**A:** Yes! Place custom videos in `Assets/Videos/Horizontal Videos/` or `Vertical Videos/` and they'll be automatically available.

### Q: What are the system requirements?
**A:** Minimum: Python 3.10, 4GB RAM, 10GB disk space. Recommended: 8GB+ RAM, SSD, dedicated GPU.

### Q: Can I integrate with N8N?
**A:** Yes! Use the REST API endpoints directly in N8N HTTP Request nodes. See N8N Integration section above.

### Q: How do I report bugs?
**A:** Open an issue on [GitHub Issues](https://github.com/HossamBalaha/Text2Video-Generation-Suite/issues) with:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- System information
- Error logs

### Q: Can I contribute?
**A:** Yes! Fork the repo, make changes, and submit a pull request. See Contributing section above.

---

## 📊 Project Statistics

- **Total Audio Tools:** 30
- **Supported Languages:** 8+
- **API Endpoints:** 30+
- **Web Pages:** 4
- **Lines of Code:** 5000+
- **Python Version:** 3.10+
- **Dependencies:** 15
- **Test Coverage:** Growing
- **Documentation Pages:** 5+

---

## 🎯 Success Stories

Share your success stories! Have you created something amazing with this project?

- 📧 Email: [Contact via GitHub](https://github.com/HossamBalaha)
- 🐦 Tweet: [@HossamBalaha](https://twitter.com/HossamBalaha)
- ⭐ Star and share this project!

---

**Ready to create professional videos at scale? Start now at `http://localhost:5000` 🚀**

*Last Updated: December 10, 2025 | Version: 2.0.0*
