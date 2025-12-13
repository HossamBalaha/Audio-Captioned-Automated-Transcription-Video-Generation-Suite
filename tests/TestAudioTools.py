"""
========================================================================
        Testing Guide for New Audio Tools
        Text2Video Generation Suite
========================================================================
Author: GitHub Copilot AI Assistant
Date: December 10, 2025
========================================================================
"""

import pytest
import requests
import json
from pathlib import Path
from typing import Tuple, Dict, Any

# Test Configuration
BASE_URL = "http://localhost:5000"
API_PREFIX = f"{BASE_URL}/api/v1"
TIMEOUT = 600  # 10 minutes timeout for long operations

# Test Audio Files (should exist in Assets/Audios/)
TEST_AUDIO_FILES = {
  "sample": "Assets/Audios/sample.mp3",
  "voice" : "Assets/Audios/voice.mp3",
  "music" : "Assets/Audios/music.mp3"
}


class AudioToolsTester:
  """
  Comprehensive testing suite for all new audio tools.
  """

  def __init__(self, base_url: str = BASE_URL):
    self.base_url = base_url
    self.api_prefix = f"{base_url}/api/v1"
    self.session = requests.Session()
    self.results = {}

  def log_result(self, tool_name: str, status: str, message: str = ""):
    """Log test result."""
    self.results[tool_name] = {
      "status"   : status,
      "message"  : message,
      "timestamp": str(Path.cwd())
    }
    print(f"[{status.upper()}] {tool_name}: {message}")

  def load_test_audio(self, filename: str) -> Tuple[str, bytes]:
    """Load a test audio file."""
    try:
      with open(filename, 'rb') as f:
        return filename, f.read()
    except FileNotFoundError:
      self.log_result(f"Load {filename}", "ERROR", "Test audio file not found")
      return None, None

  # ===== BASIC TOOLS TESTS =====

  def test_audio_duration(self):
    """Test: Get Audio Duration"""
    print("\n" + "=" * 60)
    print("Testing: Get Audio Duration")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      response = self.session.post(
        f"{self.api_prefix}/audio-duration",
        files=files,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        data = response.json()
        duration = data.get('duration')
        self.log_result(
          "Get Audio Duration",
          "PASS",
          f"Duration: {duration} seconds"
        )
      else:
        self.log_result(
          "Get Audio Duration",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Get Audio Duration", "ERROR", str(e))

  def test_audio_size(self):
    """Test: Get Audio Size"""
    print("\n" + "=" * 60)
    print("Testing: Get Audio Size")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      response = self.session.post(
        f"{self.api_prefix}/audio-size",
        files=files,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        data = response.json()
        size = data.get('size')
        self.log_result(
          "Get Audio Size",
          "PASS",
          f"Size: {size}"
        )
      else:
        self.log_result(
          "Get Audio Size",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Get Audio Size", "ERROR", str(e))

  def test_check_silence(self):
    """Test: Check Silence"""
    print("\n" + "=" * 60)
    print("Testing: Check Silence Detection")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      response = self.session.post(
        f"{self.api_prefix}/check-silence",
        files=files,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        data = response.json()
        is_silent = data.get('isSilent')
        self.log_result(
          "Check Silence",
          "PASS",
          f"Is Silent: {is_silent}"
        )
      else:
        self.log_result(
          "Check Silence",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Check Silence", "ERROR", str(e))

  def test_analyze_audio(self):
    """Test: Analyze Audio"""
    print("\n" + "=" * 60)
    print("Testing: Analyze Audio")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      response = self.session.post(
        f"{self.api_prefix}/analyze-audio",
        files=files,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        data = response.json()
        codec = data.get('codec')
        duration = data.get('duration')
        bitrate = data.get('bitrate')
        self.log_result(
          "Analyze Audio",
          "PASS",
          f"Codec: {codec}, Duration: {duration}s, Bitrate: {bitrate}bps"
        )
      else:
        self.log_result(
          "Analyze Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Analyze Audio", "ERROR", str(e))

  # ===== PROCESSING TOOLS TESTS =====

  def test_reduce_noise(self):
    """Test: Reduce Noise"""
    print("\n" + "=" * 60)
    print("Testing: Reduce Noise")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["voice"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'noiseReduction': '20'}

      response = self.session.post(
        f"{self.api_prefix}/reduce-noise",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Reduce Noise",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Reduce Noise",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Reduce Noise", "ERROR", str(e))

  def test_remove_silence(self):
    """Test: Remove Silence"""
    print("\n" + "=" * 60)
    print("Testing: Remove Silence")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["voice"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'threshold': '-50', 'duration': '0.5'}

      response = self.session.post(
        f"{self.api_prefix}/remove-silence",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Remove Silence",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Remove Silence",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Remove Silence", "ERROR", str(e))

  def test_enhance_audio(self):
    """Test: Enhance Audio"""
    print("\n" + "=" * 60)
    print("Testing: Enhance Audio")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["music"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'bassGain': '5', 'trebleGain': '3'}

      response = self.session.post(
        f"{self.api_prefix}/enhance-audio",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Enhance Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Enhance Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Enhance Audio", "ERROR", str(e))

  def test_compress_audio(self):
    """Test: Compress Audio"""
    print("\n" + "=" * 60)
    print("Testing: Compress Audio")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["music"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {
        'threshold' : '-20',
        'ratio'     : '4',
        'attack'    : '200',
        'release'   : '1000',
        'makeupGain': '0'
      }

      response = self.session.post(
        f"{self.api_prefix}/compress-audio",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Compress Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Compress Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Compress Audio", "ERROR", str(e))

  def test_convert_channels(self):
    """Test: Convert Channels"""
    print("\n" + "=" * 60)
    print("Testing: Convert Channels")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'targetChannels': '1'}  # Convert to mono

      response = self.session.post(
        f"{self.api_prefix}/convert-channels",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Convert Channels",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Convert Channels",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Convert Channels", "ERROR", str(e))

  def test_loop_audio(self):
    """Test: Loop Audio"""
    print("\n" + "=" * 60)
    print("Testing: Loop Audio")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'loopCount': '3'}

      response = self.session.post(
        f"{self.api_prefix}/loop-audio",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Loop Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Loop Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Loop Audio", "ERROR", str(e))

  def test_shift_pitch(self):
    """Test: Shift Pitch"""
    print("\n" + "=" * 60)
    print("Testing: Shift Pitch")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["voice"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'semitones': '2'}  # Shift up 2 semitones

      response = self.session.post(
        f"{self.api_prefix}/shift-pitch",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Shift Pitch",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Shift Pitch",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Shift Pitch", "ERROR", str(e))

  def test_add_echo(self):
    """Test: Add Echo"""
    print("\n" + "=" * 60)
    print("Testing: Add Echo")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["voice"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'delay': '500', 'decay': '0.5'}

      response = self.session.post(
        f"{self.api_prefix}/add-echo",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Add Echo",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Add Echo",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Add Echo", "ERROR", str(e))

  def test_adjust_stereo(self):
    """Test: Adjust Stereo Width"""
    print("\n" + "=" * 60)
    print("Testing: Adjust Stereo Width")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["music"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'width': '1.5'}  # Make stereo wider

      response = self.session.post(
        f"{self.api_prefix}/adjust-stereo",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Adjust Stereo Width",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Adjust Stereo Width",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Adjust Stereo Width", "ERROR", str(e))

  def test_generate_waveform(self):
    """Test: Generate Waveform"""
    print("\n" + "=" * 60)
    print("Testing: Generate Waveform")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["music"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'width': '1280', 'height': '240', 'colors': 'blue'}

      response = self.session.post(
        f"{self.api_prefix}/generate-waveform",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Generate Waveform",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Generate Waveform",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Generate Waveform", "ERROR", str(e))

  def test_generate_spectrum(self):
    """Test: Generate Spectrum"""
    print("\n" + "=" * 60)
    print("Testing: Generate Spectrum")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["music"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'width': '1280', 'height': '720', 'colorScheme': 'rainbow'}

      response = self.session.post(
        f"{self.api_prefix}/generate-spectrum",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Generate Spectrum",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Generate Spectrum",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Generate Spectrum", "ERROR", str(e))

  def test_transcribe_audio(self):
    """Test: Transcribe Audio"""
    print("\n" + "=" * 60)
    print("Testing: Transcribe Audio")
    print("=" * 60)
    try:
      filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES["voice"])
      if not audio_data:
        return

      files = {'audioFile': (filename, audio_data)}
      data = {'language': 'en', 'outputFormat': 'txt'}

      response = self.session.post(
        f"{self.api_prefix}/transcribe-audio",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        transcription = result.get('transcription', '')[:100]
        self.log_result(
          "Transcribe Audio",
          "PASS",
          f"Transcription: {transcription}..."
        )
      else:
        self.log_result(
          "Transcribe Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Transcribe Audio", "ERROR", str(e))

  def test_mix_audio(self):
    """Test: Mix Audio"""
    print("\n" + "=" * 60)
    print("Testing: Mix Audio")
    print("=" * 60)
    try:
      files_to_upload = []
      for key in ["sample", "voice"]:
        filename, audio_data = self.load_test_audio(TEST_AUDIO_FILES[key])
        if audio_data:
          files_to_upload.append(('audioFiles', (filename, audio_data)))

      if len(files_to_upload) < 2:
        self.log_result("Mix Audio", "SKIP", "Need at least 2 audio files")
        return

      data = {'volumes': '1.0,0.8', 'duration': 'longest'}

      response = self.session.post(
        f"{self.api_prefix}/mix-audio",
        files=files_to_upload,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Mix Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Mix Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Mix Audio", "ERROR", str(e))

  def test_crossfade_audio(self):
    """Test: Crossfade Audio"""
    print("\n" + "=" * 60)
    print("Testing: Crossfade Audio")
    print("=" * 60)
    try:
      filename1, audio_data1 = self.load_test_audio(TEST_AUDIO_FILES["sample"])
      filename2, audio_data2 = self.load_test_audio(TEST_AUDIO_FILES["music"])

      if not audio_data1 or not audio_data2:
        return

      files = {
        'firstAudio' : (filename1, audio_data1),
        'secondAudio': (filename2, audio_data2)
      }
      data = {'duration': '3'}

      response = self.session.post(
        f"{self.api_prefix}/crossfade-audio",
        files=files,
        data=data,
        timeout=TIMEOUT
      )

      if response.status_code == 200:
        result = response.json()
        self.log_result(
          "Crossfade Audio",
          "PASS",
          f"File: {result.get('filename')}"
        )
      else:
        self.log_result(
          "Crossfade Audio",
          "FAIL",
          f"Status {response.status_code}: {response.text}"
        )
    except Exception as e:
      self.log_result("Crossfade Audio", "ERROR", str(e))

  def print_summary(self):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
    failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
    errors = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
    skipped = sum(1 for r in self.results.values() if r['status'] == 'SKIP')

    total = len(self.results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Errors: {errors} ⚠")
    print(f"Skipped: {skipped} -")

    pass_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")

    if failed > 0 or errors > 0:
      print("\nFailed/Error Tests:")
      for tool, result in self.results.items():
        if result['status'] in ['FAIL', 'ERROR']:
          print(f"  - {tool}: {result['message']}")

  def run_all_tests(self):
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AUDIO TOOLS TEST SUITE")
    print("Text2Video Generation Suite")
    print("=" * 60)

    # Basic Tools
    self.test_audio_duration()
    self.test_audio_size()
    self.test_check_silence()
    self.test_analyze_audio()

    # Processing Tools
    self.test_reduce_noise()
    self.test_remove_silence()
    self.test_enhance_audio()
    self.test_compress_audio()
    self.test_convert_channels()
    self.test_loop_audio()
    self.test_shift_pitch()
    self.test_add_echo()
    self.test_adjust_stereo()
    self.test_generate_waveform()
    self.test_generate_spectrum()
    self.test_transcribe_audio()

    # Combination Tools
    self.test_mix_audio()
    self.test_crossfade_audio()

    self.print_summary()


if __name__ == "__main__":
  """
  Run the complete test suite.
  
  Usage:
      python tests/test_audio_tools.py
  
  Requirements:
      - Server running on localhost:5000
      - Test audio files in Assets/Audios/
      - requests library installed
  """
  tester = AudioToolsTester()
  tester.run_all_tests()
