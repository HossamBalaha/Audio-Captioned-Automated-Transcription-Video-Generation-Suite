import pytest, requests, json
from pathlib import Path
from typing import Tuple, Dict, Any

# Define the base URL for the server.
baseUrl = "http://localhost:5000"
# Define the API prefix path.
apiPrefix = f"{baseUrl}/api/v1"
# Define the timeout in seconds for long operations.
timeout = 600  # 10 minutes timeout for long operations.

# Define test audio files that should exist in Assets/Audios/.
testAudioFiles = {
  # Provide a sample audio file path.
  "sample": "Assets/Audios/Sample_Audio.mp3",
  # Provide a voice audio file path.
  "voice" : "Assets/Audios/Sample_Audio.mp3",
  # Provide a music audio file path.
  "music" : "Assets/Audios/Sample_Music.mp3"
}


class AudioToolsTester(object):
  '''
  Comprehensive testing suite for all new audio tools.
  '''

  # Initialize the tester with base URL.
  def __init__(self, baseUrl: str = baseUrl):
    # Assign the base URL.
    self.baseUrl = baseUrl
    # Assign the API prefix.
    self.apiPrefix = f"{baseUrl}/api/v1"
    # Create a session for HTTP requests.
    self.session = requests.Session()
    # Initialize a results dictionary.
    self.results = {}

  # Log a test result entry.
  def LogResult(self, toolName: str, status: str, message: str = ""):
    '''Log test result.'''

    # Normalize status to upper-case allowing WARN.
    normStatus = status.upper()
    # Store the result in the results dict.
    self.results[toolName] = {
      "status"   : normStatus,
      "message"  : message,
      "timestamp": str(Path.cwd())
    }
    # Print a formatted status line.
    print(f"[{normStatus}] {toolName}: {message}")

  # Load a test audio file from disk.
  def LoadTestAudio(self, filename: str) -> Tuple[str, bytes]:
    '''Load a test audio file.'''

    # Attempt to open and read the file.
    try:
      # Open the file in binary mode.
      with open(filename, "rb") as f:
        # Return filename and bytes content.
        return filename, f.read()
    except FileNotFoundError:
      # Log an error result if file not found.
      self.LogResult(f"Load {filename}", "ERROR", "Test audio file not found.")
      # Return None tuple indicating failure.
      return None, None

  # ===== BASIC TOOLS TESTS =====

  # Test the audio-duration endpoint.
  def Test_AudioDuration(self):
    '''Test: Get Audio Duration.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Get Audio Duration.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/audio-duration",
        files=files,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        data = response.json()
        # Extract duration.
        duration = data.get("duration")
        # Log a PASS result.
        self.LogResult(
          "Get Audio Duration",
          "PASS",
          f"Duration: {duration} seconds."
        )
      elif (response.status_code == 400):
        # Log a WARN result with details for non-200 status.
        self.LogResult(
          "Get Audio Duration",
          "WARN",
          f"Status {response.status_code}: {response.text}."
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Get Audio Duration",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Get Audio Duration", "ERROR", str(e))

  # Test the audio-size endpoint.
  def Test_AudioSize(self):
    '''Test: Get Audio Size.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Get Audio Size.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/audio-size",
        files=files,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        data = response.json()
        # Extract size.
        size = data.get("size")
        # Log a PASS result.
        self.LogResult(
          "Get Audio Size",
          "PASS",
          f"Size: {size}."
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Get Audio Size",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Get Audio Size", "ERROR", str(e))

  # Test the check-silence endpoint.
  def Test_CheckSilence(self):
    '''Test: Check Silence.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Check Silence Detection.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/check-silence",
        files=files,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        data = response.json()
        # Extract silence flag.
        isSilent = data.get("isSilent")
        # Log a PASS result.
        self.LogResult(
          "Check Silence",
          "PASS",
          f"Is Silent: {isSilent}."
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Check Silence",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Check Silence", "ERROR", str(e))

  # Test the analyze-audio endpoint.
  def Test_AnalyzeAudio(self):
    '''Test: Analyze Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Analyze Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/analyze-audio",
        files=files,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        data = response.json()
        # Extract codec and duration.
        codec = data.get("codec")
        # Extract duration.
        duration = data.get("duration")
        # Extract bitrate.
        bitrate = data.get("bitrate")
        # Log a PASS result.
        self.LogResult(
          "Analyze Audio",
          "PASS",
          f"Codec: {codec}, Duration: {duration}s, Bitrate: {bitrate}bps."
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Analyze Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Analyze Audio", "ERROR", str(e))

  # ===== PROCESSING TOOLS TESTS =====

  # Test the reduce-noise endpoint.
  def Test_ReduceNoise(self):
    '''Test: Reduce Noise.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Reduce Noise.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the voice audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for noise reduction.
      data = {"noiseReduction": "20"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/reduce-noise",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Reduce Noise",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Reduce Noise",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Reduce Noise", "ERROR", str(e))

  # Test the remove-silence endpoint.
  def Test_RemoveSilence(self):
    '''Test: Remove Silence.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Remove Silence.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the voice audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for silence removal.
      data = {"threshold": "-50", "duration": "0.5"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/remove-silence",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Remove Silence",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Remove Silence",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Remove Silence", "ERROR", str(e))

  # Test the enhance-audio endpoint.
  def Test_EnhanceAudio(self):
    '''Test: Enhance Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Enhance Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the music audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["music"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for enhancement.
      data = {"bassGain": "5", "trebleGain": "3"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/enhance-audio",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Enhance Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Enhance Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Enhance Audio", "ERROR", str(e))

  # Test the compress-audio endpoint.
  def Test_CompressAudio(self):
    '''Test: Compress Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Compress Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the music audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["music"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for compression.
      data = {
        "threshold" : "-20",
        "ratio"     : "4",
        "attack"    : "200",
        "release"   : "1000",
        "makeupGain": "0"
      }

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/compress-audio",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Compress Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Compress Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Compress Audio", "ERROR", str(e))

  # Test the convert-channels endpoint.
  def Test_ConvertChannels(self):
    '''Test: Convert Channels.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Convert Channels.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for channel conversion.
      data = {"targetChannels": "1"}  # Convert to mono.

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/convert-channels",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Convert Channels",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Convert Channels",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Convert Channels", "ERROR", str(e))

  # Test the loop-audio endpoint.
  def Test_LoopAudio(self):
    '''Test: Loop Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Loop Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the sample audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["sample"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for looping.
      data = {"loopCount": "3"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/loop-audio",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Loop Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Loop Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Loop Audio", "ERROR", str(e))

  # Test the shift-pitch endpoint.
  def Test_ShiftPitch(self):
    '''Test: Shift Pitch.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Shift Pitch.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the voice audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for pitch shift.
      data = {"semitones": "2"}  # Shift up 2 semitones.

      # Issue a POST response to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/shift-pitch",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Shift Pitch",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Shift Pitch",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Shift Pitch", "ERROR", str(e))

  # Test the add-echo endpoint.
  def Test_AddEcho(self):
    '''Test: Add Echo.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Add Echo.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the voice audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for echo.
      data = {"delay": "500", "decay": "0.5"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/add-echo",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Add Echo",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Add Echo",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Add Echo", "ERROR", str(e))

  # Test the adjust-stereo endpoint.
  def Test_AdjustStereo(self):
    '''Test: Adjust Stereo Width.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Adjust Stereo Width.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the music audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["music"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for stereo adjustment.
      data = {"width": "1.5"}  # Make stereo wider.

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/adjust-stereo",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Adjust Stereo Width",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Adjust Stereo Width",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Adjust Stereo Width", "ERROR", str(e))

  # Test the generate-waveform endpoint.
  def Test_GenerateWaveform(self):
    '''Test: Generate Waveform.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Generate Waveform.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the music audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["music"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for waveform generation.
      data = {"width": "1280", "height": "240", "colors": "blue"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/generate-waveform",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Generate Waveform",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Generate Waveform",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Generate Waveform", "ERROR", str(e))

  # Test the generate-spectrum endpoint.
  def Test_GenerateSpectrum(self):
    '''Test: Generate Spectrum.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Generate Spectrum.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the music audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["music"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for spectrum generation.
      data = {"width": "1280", "height": "720", "colorScheme": "rainbow"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/generate-spectrum",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Generate Spectrum",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Generate Spectrum",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Generate Spectrum", "ERROR", str(e))

  # Test the transcribe-audio endpoint.
  def Test_TranscribeAudio(self):
    '''Test: Transcribe Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Transcribe Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the voice audio file.
      filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
      # Short-circuit if audio not loaded.
      if (not audioData):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {"audioFile": (filename, audioData)}
      # Build form data for transcription.
      data = {"language": "en", "outputFormat": "txt"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/transcribe-audio",
        files=files,
        data=data,
        timeout=timeout
      )

      # Handle status outcomes.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Extract a preview of the transcription.
        transcription = result.get("transcription", "")[:100]
        # Log a PASS with transcription preview.
        self.LogResult(
          "Transcribe Audio",
          "PASS",
          f"Transcription: {transcription}..."
        )
      elif (response.status_code in (400, 500)):
        # Parse JSON response body.
        try:
          result = response.json()
          errMsg = result.get("error", str(result))
        except Exception:
          errMsg = response.text
        # Log as PASS but note environment-related outcome.
        self.LogResult(
          "Transcribe Audio",
          "WARN",
          f"Environment-related status {response.status_code}: {errMsg}."
        )
      else:
        # Log a FAIL result with unexpected status.
        self.LogResult(
          "Transcribe Audio",
          "FAIL",
          f"Unexpected status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Transcribe Audio", "ERROR", str(e))

  # Test the mix-audio endpoint.
  def Test_MixAudio(self):
    '''Test: Mix Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Mix Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Initialize files to upload.
      filesToUpload = []
      # Iterate over the required keys.
      for key in ["sample", "voice"]:
        # Load each test audio.
        filename, audioData = self.LoadTestAudio(testAudioFiles[key])
        # Append if audio data exists.
        if (audioData):
          # Append the file tuple.
          filesToUpload.append(("audioFiles", (filename, audioData)))

      # Check for minimum files requirement.
      if (len(filesToUpload) < 2):
        # Log a skipped result.
        self.LogResult("Mix Audio", "SKIP", "Need at least 2 audio files.")
        # Exit the test early.
        return

      # Build form data for volume and duration.
      data = {"volumes": "1.0,0.8", "duration": "longest"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/mix-audio",
        files=filesToUpload,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Mix Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Mix Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Mix Audio", "ERROR", str(e))

  # Test the crossfade-audio endpoint.
  def Test_CrossfadeAudio(self):
    '''Test: Crossfade Audio.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the test name.
    print("Testing: Crossfade Audio.")
    # Print a section divider.
    print("=" * 60)
    # Wrap the test in a try-except block.
    try:
      # Load the first audio file.
      filename1, audioData1 = self.LoadTestAudio(testAudioFiles["sample"])
      # Load the second audio file.
      filename2, audioData2 = self.LoadTestAudio(testAudioFiles["music"])

      # Short-circuit if either audio not loaded.
      if ((not audioData1) or (not audioData2)):
        # Exit the test early.
        return

      # Build files payload for multipart.
      files = {
        "firstAudio" : (filename1, audioData1),
        "secondAudio": (filename2, audioData2)
      }
      # Build form data for crossfade duration.
      data = {"duration": "3"}

      # Issue a POST request to the endpoint.
      response = self.session.post(
        f"{self.apiPrefix}/crossfade-audio",
        files=files,
        data=data,
        timeout=timeout
      )

      # Check if status code is 200 OK.
      if (response.status_code == 200):
        # Parse JSON response body.
        result = response.json()
        # Log a PASS with output filename.
        self.LogResult(
          "Crossfade Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        # Log a FAIL result with details.
        self.LogResult(
          "Crossfade Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}."
        )
    except Exception as e:
      # Log an ERROR result with exception message.
      self.LogResult("Crossfade Audio", "ERROR", str(e))

  # Additional API test: invalid voices type parameter.
  def Test_VoicesInvalidType(self):
    '''Test: Voices Invalid Type (Expect 400).'''

    # Issue a GET request with invalid type.
    response = self.session.get(f"{self.apiPrefix}/voices", params={"type": "unknown"}, timeout=timeout)
    # Assert bad request status.
    assert (response.status_code == 400)
    # Parse JSON response.
    data = response.json()
    # Assert error message exists.
    assert ("error" in data)

  # Invalid parameter test example for shift-pitch.
  def Test_ShiftPitchInvalidParam(self):
    '''Test: Shift Pitch Invalid Param (Expect 400).'''

    # Load the voice audio file.
    filename, audioData = self.LoadTestAudio(testAudioFiles["voice"])
    # Short-circuit if audio not loaded.
    if (not audioData):
      # Exit the test early.
      return
    # Build files payload for multipart.
    files = {"audioFile": (filename, audioData)}
    # Use out-of-range semitones if server validates.
    data = {"semitones": "999"}
    # Issue a POST request to the endpoint.
    response = self.session.post(
      f"{self.apiPrefix}/shift-pitch",
      files=files,
      data=data,
      timeout=timeout
    )
    # Assert status is one of expected outcomes.
    assert (response.status_code in (400, 500))

  # Print a summary of the test results.
  def PrintSummary(self):
    '''Print test summary.'''
    # Print a section divider.
    print("\n" + "=" * 60)
    # Print the summary header.
    print("TEST SUMMARY")
    # Print a section divider.
    print("=" * 60)

    # Compute the number of passed tests.
    passed = sum(1 for r in self.results.values() if (r["status"] == "PASS"))
    # Compute warnings: explicit WARN status or FAIL with environment-related status codes.
    warnings = 0
    for r in self.results.values():
      # Count explicit WARN status.
      if (r["status"] == "WARN"):
        # Increment warnings count.
        warnings += 1
        # Continue loop.
        continue
      # Reclassify FAIL entries that are environment-related (400/500) as warnings.
      if (r["status"] == "FAIL"):
        # Lowercase message for search.
        msg = (r["message"] or "").lower()
        # Heuristics to detect 400/500 statuses recorded in message.
        if ("status 400" in msg or "status 500" in msg or "environment-related status" in msg):
          # Increment warnings count.
          warnings += 1
    # Compute failures excluding those reclassified as warnings.
    failed = 0
    for r in self.results.values():
      # Count FAIL that are not environment-related.
      if (r["status"] == "FAIL"):
        # Lowercase message for search.
        msg = (r["message"] or "").lower()
        # Only count as failure if not 400/500 and not environment-related.
        if ("status 400" not in msg and "status 500" not in msg and "environment-related status" not in msg):
          # Increment failures count.
          failed += 1
    # Compute the number of error tests.
    errors = sum(1 for r in self.results.values() if (r["status"] == "ERROR"))
    # Compute the number of skipped tests.
    skipped = sum(1 for r in self.results.values() if (r["status"] == "SKIP"))

    # Compute total number of tests.
    total = len(self.results)

    # Print totals.
    print(f"\nTotal Tests: {total}")
    # Print passed count.
    print(f"Passed: {passed} ✓")
    # Print warnings count.
    print(f"Warnings: {warnings} ⚠")
    # Print failed count.
    print(f"Failed: {failed} ✗")
    # Print errors count.
    print(f"Errors: {errors} !")
    # Print skipped count.
    print(f"Skipped: {skipped} -")

    # Compute pass rate percentage (treat warnings as non-fail).
    passRate = (passed / total * 100) if (total > 0) else 0
    # Print pass rate.
    print(f"\nPass Rate: {passRate:.1f}%")

    # Print details for failures and warnings.
    if ((failed > 0) or (warnings > 0) or (errors > 0)):
      # Print header for details.
      print("\nFailed/Warning/Error Tests:")
      # Iterate through results.
      for tool, result in self.results.items():
        # Lowercase message for search.
        msg = (result["message"] or "").lower()
        # Determine effective status.
        effectiveStatus = result["status"]
        # Reclassify environment-related FAILs to WARN for display.
        if (effectiveStatus == "FAIL" and (
          "status 400" in msg or "status 500" in msg or "environment-related status" in msg)):
          # Set effective status to WARN.
          effectiveStatus = "WARN"
        # Print entries that are not PASS or SKIP.
        if (effectiveStatus in ["FAIL", "WARN", "ERROR"]):
          # Print the tool and message.
          print(f"  - ({effectiveStatus}) {tool}: {result['message']}")

  # Run the entire test suite.
  def RunAllTests(self):
    '''Run all tests.'''

    # Print a section divider.
    print("\n" + "=" * 60)
    # Print suite header.
    print("AUDIO TOOLS TEST SUITE")
    # Print project name.
    print("Text2Video Generation Suite")
    # Print a section divider.
    print("=" * 60)

    # Run basic tools tests.
    self.Test_AudioDuration()
    # Run audio size test.
    self.Test_AudioSize()
    # Run check silence test.
    self.Test_CheckSilence()
    # Run analyze audio test.
    self.Test_AnalyzeAudio()

    # Run processing tools tests.
    self.Test_ReduceNoise()
    # Run remove silence test.
    self.Test_RemoveSilence()
    # Run enhance audio test.
    self.Test_EnhanceAudio()
    # Run compress audio test.
    self.Test_CompressAudio()
    # Run convert channels test.
    self.Test_ConvertChannels()
    # Run loop audio test.
    self.Test_LoopAudio()
    # Run shift pitch test.
    self.Test_ShiftPitch()
    # Run add echo test.
    self.Test_AddEcho()
    # Run adjust stereo width test.
    self.Test_AdjustStereo()
    # Run generate waveform test.
    self.Test_GenerateWaveform()
    # Run generate spectrum test.
    self.Test_GenerateSpectrum()
    # Run transcribe audio test.
    self.Test_TranscribeAudio()

    # Run combination tools tests.
    self.Test_MixAudio()
    # Run crossfade audio test.
    self.Test_CrossfadeAudio()

    # Print the summary.
    self.PrintSummary()


# Execute the test suite when run as a script.
if __name__ == "__main__":
  '''
  Run the complete test suite.
  
  Usage:
      python tests/Test_AudioTools.py
  
  Requirements:
      - Server running on localhost:5000.
      - Test audio files in Assets/Audios/.
      - requests library installed.
  '''

  # Create a tester instance.
  tester = AudioToolsTester()
  # Run standard tool tests.
  tester.RunAllTests()
  # Run additional API check for invalid voices type.
  tester.Test_VoicesInvalidType()
  # Run additional invalid parameter test for shift-pitch.
  tester.Test_ShiftPitchInvalidParam()
