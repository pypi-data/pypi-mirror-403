# 05: Code Patterns and Reference

## Audio Content Message Format

### Supported Input Formats

```python
# Format 1: File path
{
    "type": "audio",
    "path": "/path/to/audio.mp3"
}

# Format 2: Base64 encoded
{
    "type": "audio",
    "base64": "SGVsbG8gV29ybGQ...",
    "media_type": "audio/mpeg"
}

# Format 3: Raw bytes
{
    "type": "audio",
    "bytes": b"raw audio bytes",
    "media_type": "audio/wav"
}

# Format 4: Data URL (like image_url)
{
    "type": "audio_url",
    "audio_url": {
        "url": "data:audio/mp3;base64,SGVsbG8..."
    }
}
```

### Complete Message Example

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Please transcribe this audio clip."},
            {"type": "audio", "path": "/path/to/recording.mp3"}
        ]
    }
]

response = provider.chat(messages, model="gemini-2.0-flash")
```

## Supported Audio Formats

| Extension | MIME Type | Gemini | OpenAI | Whisper |
|-----------|-----------|--------|--------|---------|
| `.mp3` | `audio/mpeg` | ✅ | ✅ | ✅ |
| `.wav` | `audio/wav` | ✅ | ✅ | ✅ |
| `.m4a` | `audio/mp4` | ✅ | ✅ | ✅ |
| `.ogg` | `audio/ogg` | ✅ | ⚠️ | ✅ |
| `.flac` | `audio/flac` | ✅ | ❌ | ✅ |
| `.webm` | `audio/webm` | ✅ | ❌ | ⚠️ |
| `.aiff` | `audio/aiff` | ✅ | ❌ | ✅ |

## Error Handling Patterns

### Hierarchical Error Strategy

| Level | Strategy | Example |
|-------|----------|---------|
| **Utility Functions** | Raise exceptions | `FileNotFoundError`, `ValueError` |
| **Field Classes** | Raise + validation method | `field.validate() → (bool, error_msg)` |
| **Providers** | Warn + skip | Log warning, continue without audio |
| **Workflow Nodes** | Structured errors | Return `{"error": ..., "code": ...}` |

### Example Implementations

```python
# Level 1: Utility functions - RAISE
def encode_audio(audio_path: str) -> str:
    """Raises FileNotFoundError, IOError."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    # ...

# Level 2: Field classes - RAISE + VALIDATE
class AudioField:
    def load(self, source) -> "AudioField":
        """Raises ValueError, FileNotFoundError."""

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Returns (is_valid, error_message) - never raises."""
        if self._size_bytes > self.max_size_mb * 1024 * 1024:
            return False, f"Audio size exceeds {self.max_size_mb}MB limit"
        return True, None

# Level 3: Providers - WARN + SKIP
def _convert_audio_content(self, item: dict) -> Optional[Part]:
    """Returns None on failure, logs warning."""
    try:
        return self._encode_audio_part(item)
    except Exception as e:
        import warnings
        warnings.warn(f"Audio encoding failed: {e}")
        return None
```

## AudioField Usage Patterns

### Loading Audio

```python
from kaizen.signatures.multi_modal import AudioField

# From file path
field = AudioField()
field.load("/path/to/audio.mp3")

# From bytes
field = AudioField()
field.load(audio_bytes)

# With configuration
field = AudioField(
    max_duration_sec=600.0,  # 10 minutes
    max_size_mb=25.0,
    formats=["mp3", "wav", "m4a", "ogg"]
)
field.load("/path/to/audio.mp3")
```

### Converting to Base64

```python
# Get data URL for API transmission
data_url = field.to_base64()
# Returns: "data:audio/mp3;base64,SGVsbG8..."

# Use in message content
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Analyze this audio"},
        {"type": "audio", "base64": field.to_base64().split(",")[1], "media_type": "audio/mp3"}
    ]
}]
```

### Validation

```python
# Check if field is valid
is_valid, error = field.validate()
if not is_valid:
    print(f"Audio validation failed: {error}")
```

## Provider-Specific Notes

### Google Gemini

- Supports native audio input via `types.Part.from_bytes()`
- Models: `gemini-2.0-flash`, `gemini-2.5-flash`
- Max size: 20MB inline
- Max duration: 9.5 hours

### OpenAI GPT-4o

- Uses different input format (`input_audio` type)
- Model: `gpt-4o-audio-preview`
- Research required for exact format

### Local Whisper

- Uses `WhisperProcessor` class
- Separate from provider audio handling
- For transcription-only use cases

## Security Considerations

### Safe Logging

```python
# ❌ NEVER LOG:
logger.info(f"Audio content: {audio_base64}")

# ✅ SAFE TO LOG:
logger.info(f"Processing audio: {len(audio_bytes)} bytes, type: {media_type}")
```

### Size Validation

Always validate size before processing:

```python
from kaizen.nodes.ai.audio_utils import validate_audio_size

is_valid, error = validate_audio_size(audio_path, max_size_mb=25.0)
if not is_valid:
    raise ValueError(error)
```
