# 03: Implementation Phases

## Phase 0: Infrastructure (Do First) - 1 hour

### 0.1 Add Warning for Unhandled Content Types

**File**: `kaizen/nodes/ai/ai_providers.py`
**Location**: End of content type handling in `_convert_messages_to_contents()`

```python
# After all elif branches for text, image, image_url
else:
    import warnings
    warnings.warn(
        f"Unhandled content type in message: {item.get('type')}. "
        "Content will be silently skipped.",
        UserWarning,
        stacklevel=2
    )
```

**Rationale**: Prevents future silent failures. Must be done FIRST so any remaining gaps are visible during testing.

---

## Phase 1: Core Audio Infrastructure - 1 day

### 1.1 Create audio_utils.py

**File**: `kaizen/nodes/ai/audio_utils.py`

```python
"""Audio utilities for AI providers - lazy loaded to avoid overhead.

Mirrors vision_utils.py pattern for consistency.
"""

from pathlib import Path
from typing import Optional, Tuple


def encode_audio(audio_path: str) -> str:
    """
    Encode audio file to base64 string.

    Args:
        audio_path: Path to the audio file

    Returns:
        Base64 encoded string of the audio

    Raises:
        FileNotFoundError: If audio file doesn't exist
        IOError: If unable to read the audio file
    """
    import base64

    audio_path = Path(audio_path).resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")
    except Exception as e:
        raise IOError(f"Failed to read audio file: {e}")


def get_audio_media_type(audio_path: str) -> str:
    """
    Get media type from file extension.

    Args:
        audio_path: Path to the audio file

    Returns:
        Media type string (e.g., "audio/mpeg")
    """
    ext = Path(audio_path).suffix.lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".opus": "audio/opus",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
        ".wma": "audio/x-ms-wma",
        ".aiff": "audio/aiff",
    }
    return media_types.get(ext, "audio/mpeg")


def validate_audio_size(
    audio_path: str, max_size_mb: float = 25.0
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio file size.

    Args:
        audio_path: Path to the audio file
        max_size_mb: Maximum allowed size in megabytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    import os

    try:
        size_bytes = os.path.getsize(audio_path)
        size_mb = size_bytes / (1024 * 1024)

        if size_mb > max_size_mb:
            return False, f"Audio size {size_mb:.1f}MB exceeds maximum {max_size_mb}MB"

        return True, None
    except Exception as e:
        return False, f"Failed to check audio size: {e}"
```

### 1.2 Add Audio Handling to GoogleGeminiProvider

**File**: `kaizen/nodes/ai/ai_providers.py`
**Location**: `_convert_messages_to_contents()` method, after image_url handling

```python
elif item.get("type") == "audio":
    # Handle audio content
    if "path" in item:
        from .audio_utils import encode_audio, get_audio_media_type
        base64_data = encode_audio(item["path"])
        media_type = get_audio_media_type(item["path"])
        parts.append(
            types.Part.from_bytes(
                data=__import__("base64").b64decode(base64_data),
                mime_type=media_type,
            )
        )
    elif "base64" in item:
        media_type = item.get("media_type", "audio/mpeg")
        parts.append(
            types.Part.from_bytes(
                data=__import__("base64").b64decode(item["base64"]),
                mime_type=media_type,
            )
        )
    elif "bytes" in item:
        media_type = item.get("media_type", "audio/mpeg")
        parts.append(
            types.Part.from_bytes(
                data=item["bytes"],
                mime_type=media_type,
            )
        )
```

### 1.3 Add audio_url Support (Like image_url)

```python
elif item.get("type") == "audio_url":
    url = item.get("audio_url", {}).get("url", "")
    if url.startswith("data:audio"):
        import re
        match = re.match(r"data:([^;]+);base64,(.+)", url, re.DOTALL)
        if match:
            media_type, base64_data = match.groups()
            parts.append(
                types.Part.from_bytes(
                    data=__import__("base64").b64decode(base64_data),
                    mime_type=media_type,
                )
            )
```

---

## Phase 2: Provider Parity - 1 day

### 2.1 Add AudioField.to_base64()

**File**: `kaizen/signatures/multi_modal.py`
**Location**: `AudioField` class

```python
def to_base64(self) -> str:
    """Convert audio to base64 string with data URL prefix.

    Returns:
        Data URL string (e.g., "data:audio/mp3;base64,...")

    Raises:
        ValueError: If no audio data is loaded
    """
    if not self._data:
        raise ValueError("No audio data loaded")
    import base64
    b64_str = base64.b64encode(self._data).decode("utf-8")
    return f"data:audio/{self._format};base64,{b64_str}"
```

### 2.2 Add Audio Handling to OpenAIProvider

**Note**: OpenAI GPT-4o uses different audio input format. Research required.

```python
# OpenAI format may be:
{
    "type": "input_audio",
    "input_audio": {
        "data": "<base64>",
        "format": "wav"  # or mp3
    }
}
```

### 2.3 Add Audio Handling to AzureAIFoundryProvider

Follow OpenAI pattern if using Azure OpenAI endpoints.

### 2.4 Update MultiModalSignature.format_for_ollama()

```python
@classmethod
def format_for_ollama(cls, **inputs) -> Dict[str, Any]:
    text_parts = []
    images = []
    audios = []  # NEW

    for field_name, value in inputs.items():
        if isinstance(value, ImageField):
            if value._data:
                images.append(value.to_base64())
        elif isinstance(value, AudioField):  # NEW
            if value._data:
                audios.append(value.to_base64())
        elif isinstance(value, str):
            text_parts.append(f"{field_name}: {value}")

    result = {"content": " ".join(text_parts)}
    if images:
        result["images"] = images
    if audios:  # NEW
        result["audios"] = audios

    return result
```

---

## Phase 3: Testing - 1 day

### 3.1 Tier 1: Unit Tests

**Directory**: `tests/unit/audio/`

- `test_audio_field.py` - AudioField.to_base64() tests
- `test_audio_utils.py` - encode_audio, get_audio_media_type, validate_audio_size

### 3.2 Tier 2: Integration Tests

**Directory**: `tests/integration/audio/`

- `test_audio_provider_integration.py` - Real Gemini/OpenAI API calls with audio
- `test_whisper_integration.py` - Real Whisper transcription

**Requirements**: Real API keys, real audio files, NO MOCKING

### 3.3 Tier 3: E2E Tests

**Directory**: `tests/e2e/audio/`

- `test_audio_agent_e2e.py` - Complete MultiModalAgent workflows with audio

### 3.4 Test Audio Fixtures

**Directory**: `tests/fixtures/audio/`

| File | Duration | Content |
|------|----------|---------|
| `english_speech.wav` | 5-10s | Clear English speech |
| `music_sample.mp3` | 10s | Instrumental music |
| `silence.wav` | 3s | Silent audio |

---

## Phase 4: Documentation Updates (Post-Implementation)

1. Update `CLAUDE.md` with audio support documentation
2. Update `.claude/agents/frameworks/kaizen-specialist.md`
3. Update `.claude/skills/04-kaizen/`
4. Update `sdk-users/apps/kaizen` user documentation
