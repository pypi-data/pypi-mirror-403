# 04: Testing Strategy

## Overview

3-tier testing strategy following the **NO MOCKING policy for Tiers 2-3**.

## Test Coverage Matrix

| Component | Tier 1 | Tier 2 | Tier 3 |
|-----------|--------|--------|--------|
| AudioField.load() | Unit | - | - |
| AudioField.to_base64() | Unit | - | - |
| AudioField.validate() | Unit | - | - |
| audio_utils.encode_audio() | Unit | - | - |
| audio_utils.get_audio_media_type() | Unit | - | - |
| audio_utils.validate_audio_size() | Unit | - | - |
| GoogleGeminiProvider + audio | Mock | Real API | - |
| OpenAIProvider + audio | Mock | Real API | - |
| WhisperProcessor.transcribe() | - | Real Whisper | - |
| MultiModalAgent.run(audio=...) | - | - | Real E2E |
| Batch audio processing | - | - | Real E2E |
| Error handling | Unit | - | Real E2E |

## Tier 1: Unit Tests

**Location**: `tests/unit/audio/`
**Speed**: <1 second per test
**Mocking**: Allowed for external services

### Test Files

```
tests/unit/audio/
├── test_audio_field.py      # AudioField.to_base64() tests
├── test_audio_utils.py      # audio_utils functions
└── test_provider_conversion.py  # Message conversion (mocked)
```

### Key Test Cases

```python
class TestAudioFieldToBase64:
    def test_to_base64_returns_valid_data_url(self, tmp_path)
    def test_to_base64_without_data_raises_error(self)
    def test_to_base64_preserves_format_in_mime_type(self, tmp_path)

class TestAudioUtilsFunctions:
    def test_encode_audio_from_file_path(self, tmp_path)
    def test_encode_audio_file_not_found(self)
    def test_get_audio_media_type_detection(self)
    def test_validate_audio_size_within_limit(self, tmp_path)
    def test_validate_audio_size_exceeds_limit(self, tmp_path)

class TestEdgeCases:
    def test_empty_audio_file(self, tmp_path)
    def test_corrupted_audio_header(self, tmp_path)
    def test_unsupported_format(self, tmp_path)
    def test_unicode_filename(self, tmp_path)
```

## Tier 2: Integration Tests (NO MOCKING)

**Location**: `tests/integration/audio/`
**Speed**: <30 seconds per test
**Requirements**: Real API keys

### Prerequisites

```bash
# Required environment variables
GOOGLE_API_KEY=your_key
OPENAI_API_KEY=your_key

# Required packages
pip install faster-whisper
```

### Test Files

```
tests/integration/audio/
├── test_audio_provider_integration.py  # Real API calls
├── test_whisper_integration.py         # Real Whisper
└── conftest.py                         # Audio fixtures
```

### Key Test Cases

```python
@pytest.mark.skipif(not has_google_api(), reason="GOOGLE_API_KEY not set")
class TestGeminiAudioIntegration:
    def test_gemini_transcribes_english_speech(self, english_audio)
    def test_gemini_describes_music(self, music_audio)
    def test_gemini_audio_with_follow_up_question(self, english_audio)

@pytest.mark.skipif(not has_openai_api(), reason="OPENAI_API_KEY not set")
class TestOpenAIAudioIntegration:
    def test_openai_processes_audio_input(self, english_audio)

class TestWhisperIntegration:
    def test_whisper_transcribes_english(self, english_audio)
    def test_whisper_segments_have_timestamps(self, english_audio)
```

### Verification Strategy: Audio Actually Processed

**CRITICAL**: Tests must verify audio was processed, not silently dropped.

```python
# Negative assertion pattern
failure_indicators = [
    "cannot process audio",
    "unable to hear",
    "no audio",
    "don't have access to audio",
]
response_lower = response["content"].lower()
for indicator in failure_indicators:
    assert indicator not in response_lower, \
        f"Audio processing failed: found '{indicator}' in response"
```

## Tier 3: E2E Tests (NO MOCKING)

**Location**: `tests/e2e/audio/`
**Speed**: <60 seconds per test
**Focus**: User-level workflows

### Test Files

```
tests/e2e/audio/
├── test_audio_agent_e2e.py     # MultiModalAgent workflows
├── test_audio_error_handling.py # Error scenarios
└── conftest.py                  # E2E fixtures
```

### Key Test Cases

```python
class TestMultiModalAgentAudioE2E:
    def test_e2e_audio_transcription_workflow(self, english_audio)
    def test_e2e_audio_qa_workflow(self, english_audio)
    def test_e2e_batch_audio_processing(self, audio_fixtures_dir)
    def test_e2e_audio_with_cost_tracking(self, english_audio)

class TestAudioErrorHandlingE2E:
    def test_e2e_nonexistent_audio_file(self)
    def test_e2e_unsupported_audio_format(self, tmp_path)
```

## Test Audio Fixtures

**Location**: `tests/fixtures/audio/`

| File | Duration | Content | Purpose |
|------|----------|---------|---------|
| `english_speech.wav` | 5-10s | Clear English speech | Transcription tests |
| `music_sample.mp3` | 10s | Instrumental music | Music description tests |
| `silence.wav` | 3s | Silent audio | Edge case handling |

**IMPORTANT**: Use REAL recorded audio, not synthesized sine waves.

## Running Tests

```bash
# Tier 1: Unit tests (fast, no API keys needed)
pytest tests/unit/audio/ -v --timeout=1

# Tier 2: Integration tests (requires API keys)
GOOGLE_API_KEY=your_key pytest tests/integration/audio/ -v --timeout=30

# Tier 3: E2E tests (requires API keys + fixtures)
GOOGLE_API_KEY=your_key OPENAI_API_KEY=your_key \
  pytest tests/e2e/audio/ -v --timeout=60

# All audio tests
pytest tests/unit/audio tests/integration/audio tests/e2e/audio -v
```

## Test Intent Validation

All tests must validate **user intent**, not just technical assertions.

### Good Test (Intent-Based)

```python
def test_gemini_transcribes_english_speech(self, english_audio):
    """
    USER INTENT: When I send English speech to Gemini, it should
    transcribe or describe the audio content accurately.

    VERIFICATION: Response must contain evidence the audio was processed,
    not a generic "I can't process audio" response.
    """
    # ... test implementation ...

    # Intent validation
    assert response["content"], "Response content should not be empty"
    assert len(response["content"]) > 20, "Response should have substantial content"
```

### Bad Test (Technical-Only)

```python
def test_gemini_audio(self, english_audio):
    # ❌ Just checks technical details, not user intent
    response = provider.chat(messages)
    assert response is not None
    assert "content" in response
```
