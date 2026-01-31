"""Audio types for STT (transcription) and TTS (speech)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# STT (Transcription) Response Types
# =============================================================================


class TranscriptionResponse(BaseModel):
    """Response from transcription endpoint (json format).

    Returned when response_format="json" (default).
    """

    text: str = Field(description="Transcribed text")


class TranscriptionSegment(BaseModel):
    """A single transcription segment with timing."""

    id: int = Field(description="Segment index")
    seek: int = Field(default=0, description="Seek offset in samples")
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Transcribed text for this segment")
    tokens: list[int] = Field(default_factory=list, description="Token IDs")
    temperature: float = Field(default=0, description="Sampling temperature used")
    avg_logprob: float = Field(default=0, description="Average log probability")
    compression_ratio: float = Field(default=0, description="Compression ratio")
    no_speech_prob: float = Field(default=0, description="Probability of no speech")


class VerboseTranscriptionResponse(BaseModel):
    """Response from transcription endpoint (verbose_json format).

    Returned when response_format="verbose_json".
    Includes additional metadata: detected language, duration, segments.
    """

    text: str = Field(description="Full transcribed text")
    language: str | None = Field(default=None, description="Detected language code (e.g. 'en')")
    duration: float | None = Field(default=None, description="Audio duration in seconds")
    segments: list[TranscriptionSegment] | None = Field(
        default=None, description="Word-level timing segments"
    )


# Type alias for response_format parameter
TranscriptionResponseFormat = Literal["json", "verbose_json", "text", "srt", "vtt"]


# =============================================================================
# TTS (Speech) Types
# =============================================================================

# Valid voice identifiers
TTSVoice = Literal[
    "alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"
]

# Valid audio output formats
TTSResponseFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]


class SpeechRequest(BaseModel):
    """Request body for speech synthesis.

    Mirrors the OpenAI-compatible TTS API request format.
    """

    model: str = Field(
        default="tts-1",
        description="TTS model to use (tts-1, tts-1-hd, gpt-4o-mini-tts, or tier alias)",
    )
    input: str = Field(
        description="Text to synthesize (max 4096 characters)",
        max_length=4096,
    )
    voice: str = Field(
        default="nova",
        description="Voice: alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer",
    )
    response_format: TTSResponseFormat = Field(
        default="mp3",
        description="Output audio format",
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Playback speed (0.25 to 4.0)",
    )
    instructions: str | None = Field(
        default=None,
        description="Custom voice instructions (for gpt-4o-mini-tts)",
    )
    stream: bool = Field(
        default=False,
        description="If true, return SSE stream with PCM audio chunks + real-time analysis",
    )


# =============================================================================
# TTS (Speech) Response Types — Audio + Analysis
# =============================================================================


class AudioAnalysisFrame(BaseModel):
    """Single analysis frame for audio visualization."""

    t: float = Field(description="Timestamp in seconds")
    rms: float = Field(description="RMS amplitude, normalized 0..1")
    peak: float = Field(description="Peak amplitude, normalized 0..1")
    db: float = Field(description="Decibels, clamped to [-60, 0]")
    bands: dict[str, float] = Field(
        description="Frequency band energy: low/mid/high, normalized 0..1",
    )


class AudioAnalysis(BaseModel):
    """Audio analysis timeline for visualization.

    Contains per-frame amplitude, decibel, and frequency data
    aligned with the audio timeline. Used to drive frontend
    animations (e.g., 3D orb deformation) in sync with speech.
    """

    sample_rate: int = Field(description="Audio sample rate in Hz")
    frame_size_ms: int = Field(description="Analysis frame size in milliseconds")
    duration_s: float = Field(description="Total audio duration in seconds")
    frames: list[AudioAnalysisFrame] = Field(description="Per-frame analysis data")


class SpeechResponse(BaseModel):
    """Response from speech endpoint with audio and analysis metadata.

    Contains base64-encoded audio bytes and per-frame analysis data
    for visualization.

    Example:
        ```python
        response = client.audio.speech(input="Hello!", voice="nova")

        # Get raw audio bytes
        audio_bytes = response.audio_bytes
        Path("output.mp3").write_bytes(audio_bytes)

        # Access analysis for visualization
        for frame in response.analysis.frames:
            print(f"t={frame.t:.2f}s rms={frame.rms:.3f} db={frame.db:.1f}")
        ```
    """

    audio: str = Field(description="Base64-encoded audio bytes")
    content_type: str = Field(description="Audio MIME type, e.g. audio/mpeg")
    analysis: AudioAnalysis

    @property
    def audio_bytes(self) -> bytes:
        """Decode base64 audio to raw bytes."""
        import base64
        return base64.b64decode(self.audio)


# =============================================================================
# TTS (Speech) SSE Streaming Types
# =============================================================================


class SpeechStreamChunk(BaseModel):
    """Single SSE chunk event with audio and real-time analysis.

    Yielded by ``speech_stream()`` for each chunk of audio data.
    Audio format depends on ``response_format`` (default MP3, or PCM).

    Example:
        ```python
        for chunk in client.audio.speech_stream(input="Hello!", voice="nova"):
            audio = chunk.audio_bytes  # MP3 or PCM depending on format
            for frame in chunk.analysis:
                print(f"t={frame.t:.2f}s rms={frame.rms:.3f}")
        ```
    """

    audio: str = Field(description="Base64-encoded audio bytes (MP3 or PCM)")
    analysis: list[AudioAnalysisFrame] = Field(
        description="Analysis frames for this chunk (typically 1-8 per ~4KB chunk)",
    )

    @property
    def audio_bytes(self) -> bytes:
        """Decode base64 audio to raw bytes."""
        import base64
        return base64.b64decode(self.audio)


class SpeechStreamDone(BaseModel):
    """Final SSE event signaling stream completion.

    The last item yielded by ``speech_stream()``.
    """

    duration_s: float = Field(description="Total audio duration in seconds")
    total_chunks: int = Field(description="Number of audio chunks sent")
    sample_rate: int = Field(description="Audio sample rate in Hz")
    format: str = Field(description="Audio format of streamed chunks (mp3, pcm)")


# =============================================================================
# Audio Model Info (from /v1/audio/models)
# =============================================================================


class AudioModelInfo(BaseModel):
    """Audio model information for listing."""

    id: str = Field(description="Model identifier")
    type: str = Field(description="Model type: stt or tts")
    owned_by: str = Field(default="", description="Model owner/provider")
    supports_streaming: bool = Field(default=False)
    supported_languages: list[str] = Field(default_factory=list)
    supported_formats: list[str] = Field(default_factory=list)
    voices: list[str] = Field(default_factory=list)
    supports_instructions: bool = Field(default=False)
    pricing: dict = Field(default_factory=dict)


class AudioModelsResponse(BaseModel):
    """Response from audio models listing."""

    data: list[AudioModelInfo]


__all__ = [
    # STT types
    "TranscriptionResponse",
    "TranscriptionSegment",
    "VerboseTranscriptionResponse",
    "TranscriptionResponseFormat",
    # TTS types
    "SpeechRequest",
    "TTSVoice",
    "TTSResponseFormat",
    # TTS response types
    "AudioAnalysisFrame",
    "AudioAnalysis",
    "SpeechResponse",
    # TTS streaming types
    "SpeechStreamChunk",
    "SpeechStreamDone",
    # Model info types
    "AudioModelInfo",
    "AudioModelsResponse",
]
