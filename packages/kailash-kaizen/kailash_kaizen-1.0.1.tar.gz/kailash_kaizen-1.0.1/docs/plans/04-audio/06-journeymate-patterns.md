# 06: JourneyMate Voice Patterns (Reference)

## Overview

Analysis of JourneyMate backend voice/audio implementation patterns that can inform Kaizen improvements.

## Architecture Patterns Found

### 1. Layered Fallback (NOT Silent Failures)

```python
# Tier 1: Try Deepgram (100-200ms, fastest)
# Tier 2: Fall back to Whisper (400ms)
# Tier 3: Raise error (propagate to caller)

async def transcribe(audio_data: bytes) -> str:
    if self._deepgram_available:
        try:
            return await self._transcribe_deepgram(audio_data)
        except Exception as e:
            logger.warning(f"Deepgram failed: {e}, falling back to Whisper")
            return await self._transcribe_whisper(audio_data)
    else:
        return await self._transcribe_whisper(audio_data)
```

**Key Insight**: Errors are logged, fallbacks attempted, final failures propagate.

### 2. Streaming Architecture

All audio operations use async generators for low-latency:

```python
async for chunk in tts.generate_stream(text):
    # Stream to client immediately
    await websocket.send_json({
        "type": "audio.chunk",
        "data": base64.b64encode(chunk).decode()
    })
```

**Benefits**:
- Low-latency playback (start before full response)
- Interruption handling (`if not self._is_generating: break`)
- Resource efficiency (no buffering full audio)

### 3. Provider-Specific Formats

| Provider | Input | Output | Transport |
|----------|-------|--------|-----------|
| Deepgram STT | Raw PCM16 bytes | Text | Direct bytes |
| Whisper STT | Temp WAV file | Text | File handle |
| ElevenLabs TTS | Text | PCM16 stream | Binary chunks |
| OpenAI Realtime | Base64 PCM16 | Base64 PCM16 | WebSocket JSON |

### 4. Adaptive Voice Activity Detection

```python
vad = SileroVAD(min_silence_ms=1500)  # Standard
vad.set_adaptive_mode(True)            # Emotional: 3s silence
```

**Application**: Context-aware thresholds based on domain.

### 5. OpenAI Realtime API Integration

```python
await realtime.session.update(session={
    "modalities": ["text", "audio"],
    "voice": "shimmer",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": {"model": "whisper-1"},
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.5,
        "silence_duration_ms": 1500
    }
})
```

### 6. Metadata Capture

```python
@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    is_final: bool
    language: Optional[str] = None
```

Simple but informative for understanding transcription quality.

## Patterns to Adopt in Kaizen

| Pattern | JourneyMate | Kaizen Improvement |
|---------|-------------|-------------------|
| **Error Handling** | Layered fallback | Add warning for unhandled types |
| **Streaming** | Async generators | Consider for large audio files |
| **Metadata** | TranscriptionResult | Add to AudioField response |
| **Adaptive Mode** | Context thresholds | Could extend to MultiModalAgent |

## Patterns to Improve Over JourneyMate

| Area | JourneyMate | Kaizen Should Do |
|------|-------------|------------------|
| **Provider Abstraction** | Direct service coupling | Create AudioProvider interface |
| **Circuit Breaker** | Not implemented | Add for provider failures |
| **Error Types** | Generic Exception | Structured error types |
| **Metrics** | None | Add latency/failure tracking |
| **Caching** | None | Cache provider availability |

## Key Files Examined

- `journeymate-backend/src/aihub/services/voice/stt.py`
- `journeymate-backend/src/aihub/services/voice/tts.py`
- `journeymate-backend/src/aihub/services/voice/vad.py`
- `journeymate-backend/src/aihub/api/routers/voice.py`
