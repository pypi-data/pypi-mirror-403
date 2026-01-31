"""Audio tool for SDKRouter - STT (transcriptions) and TTS (speech).

Provides both synchronous and asynchronous audio capabilities
via OpenAI-compatible endpoints on the audio backend.

Example:
    from sdkrouter import SDKRouter, AudioModel

    client = SDKRouter(api_key="...")

    # Speech-to-text (transcription)
    with open("recording.mp3", "rb") as f:
        result = client.audio.transcribe(
            file=f.read(),
            model=AudioModel.cheap(),
        )
    print(result.text)

    # Text-to-speech (returns audio + analysis)
    response = client.audio.speech(
        input="Hello, world!",
        model=AudioModel.quality(),
        voice="nova",
    )
    Path("output.mp3").write_bytes(response.audio_bytes)

    # Access analysis for visualization
    for frame in response.analysis.frames:
        print(f"t={frame.t:.2f}s rms={frame.rms:.3f}")
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from .._api.client import BaseResource, AsyncBaseResource
from .._types.audio import (
    SpeechResponse,
    SpeechStreamChunk,
    SpeechStreamDone,
    TranscriptionResponse,
    TranscriptionResponseFormat,
    TTSResponseFormat,
    VerboseTranscriptionResponse,
)
from ..exceptions import handle_api_errors, async_api_error_handler

if TYPE_CHECKING:
    from .._config import SDKConfig

logger = logging.getLogger(__name__)

# MIME types for common audio file extensions
AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".opus": "audio/opus",
}


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    return AUDIO_MIME_TYPES.get(ext, "application/octet-stream")


def _resolve_file(
    file: bytes | str | Path,
    filename: str | None,
) -> tuple[bytes, str]:
    """Resolve file input to (bytes, filename) tuple."""
    if isinstance(file, (str, Path)):
        path = Path(file)
        resolved_filename = filename or path.name
        file_bytes = path.read_bytes()
    else:
        resolved_filename = filename or "audio.mp3"
        file_bytes = file
    return file_bytes, resolved_filename


class AudioResource(BaseResource):
    """Audio tool (sync) - STT transcription and TTS speech.

    Uses the audio backend (audio_url) for OpenAI-compatible audio endpoints.

    Example:
        ```python
        from sdkrouter import SDKRouter, AudioModel

        client = SDKRouter(api_key="your-api-key")

        # Transcribe audio file
        result = client.audio.transcribe("audio.mp3")
        print(result.text)

        # Generate speech with analysis
        response = client.audio.speech(input="Hello!", voice="nova")
        Path("output.mp3").write_bytes(response.audio_bytes)

        # Use analysis for visualization
        for frame in response.analysis.frames:
            print(f"rms={frame.rms:.3f} bands={frame.bands}")
        ```
    """

    def __init__(self, config: "SDKConfig"):
        super().__init__(config, use_audio_url=True)

    def transcribe(
        self,
        file: bytes | str | Path,
        *,
        model: str = "whisper-1",
        language: str | None = None,
        response_format: TranscriptionResponseFormat = "json",
        temperature: float = 0,
        filename: str | None = None,
    ) -> TranscriptionResponse | VerboseTranscriptionResponse | str:
        """
        Transcribe audio to text (STT).

        Args:
            file: Audio data as bytes, file path string, or Path object.
            model: STT model or tier alias ("@cheap", "@quality"). Default: "whisper-1"
            language: ISO 639-1 language code (e.g. "en", "ja"). Optional.
            response_format: "json" -> TranscriptionResponse,
                "verbose_json" -> VerboseTranscriptionResponse,
                "text"/"srt"/"vtt" -> raw string.
            temperature: Sampling temperature (0 to 1). Default: 0
            filename: Filename hint for the uploaded audio.

        Returns:
            TranscriptionResponse, VerboseTranscriptionResponse, or str.
        """
        file_bytes, resolved_filename = _resolve_file(file, filename)

        files = {
            "file": (resolved_filename, file_bytes, _guess_mime_type(resolved_filename)),
        }
        data: dict = {
            "model": model,
            "response_format": response_format,
            "temperature": str(temperature),
        }
        if language:
            data["language"] = language

        logger.debug(
            "Transcribe: model=%s, format=%s, file=%s (%d bytes)",
            model, response_format, resolved_filename, len(file_bytes),
        )

        with handle_api_errors():
            response = self._http_client.post(
                "/v1/audio/transcriptions",
                data=data,
                files=files,
            )
            response.raise_for_status()

        if response_format in ("text", "srt", "vtt"):
            return response.text
        elif response_format == "verbose_json":
            return VerboseTranscriptionResponse.model_validate(response.json())
        else:
            return TranscriptionResponse.model_validate(response.json())

    def speech(
        self,
        input: str,
        *,
        model: str = "tts-1",
        voice: str = "nova",
        response_format: TTSResponseFormat = "mp3",
        speed: float = 1.0,
        instructions: str | None = None,
    ) -> SpeechResponse:
        """
        Generate speech from text (TTS).

        Returns a SpeechResponse containing base64 audio and per-frame
        analysis metadata for visualization.

        Args:
            input: Text to synthesize (max 4096 characters).
            model: TTS model or tier alias ("@cheap", "@quality").
            voice: Voice: alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer.
            response_format: Audio format: mp3, opus, aac, flac, wav, pcm.
            speed: Playback speed (0.25 to 4.0). Default: 1.0
            instructions: Custom voice instructions (for gpt-4o-mini-tts).

        Returns:
            SpeechResponse with .audio_bytes property and .analysis data.
        """
        json_body: dict = {
            "model": model,
            "input": input,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }
        if instructions is not None:
            json_body["instructions"] = instructions

        logger.debug(
            "Speech: model=%s, voice=%s, format=%s, input_len=%d",
            model, voice, response_format, len(input),
        )

        with handle_api_errors():
            response = self._http_client.post(
                "/v1/audio/speech",
                json=json_body,
            )
            response.raise_for_status()

        return SpeechResponse.model_validate(response.json())

    def speech_stream(
        self,
        input: str,
        *,
        model: str = "tts-1",
        voice: str = "nova",
        response_format: TTSResponseFormat = "mp3",
        speed: float = 1.0,
        instructions: str | None = None,
    ) -> Iterator[SpeechStreamChunk | SpeechStreamDone]:
        """
        Generate speech from text with SSE streaming (sync).

        Streams audio chunks with real-time analysis frames.
        Audio format defaults to MP3; set response_format="pcm" for raw PCM.
        The final yielded item is a SpeechStreamDone with summary info.

        Args:
            input: Text to synthesize (max 4096 characters).
            model: TTS model or tier alias.
            voice: Voice identifier. Default: "nova"
            response_format: Audio format for chunks: "mp3" (default) or "pcm".
            speed: Playback speed (0.25 to 4.0). Default: 1.0
            instructions: Custom voice instructions (for gpt-4o-mini-tts).

        Yields:
            SpeechStreamChunk for each audio chunk, then SpeechStreamDone.

        Example:
            ```python
            for item in client.audio.speech_stream(input="Hello!", voice="nova"):
                if isinstance(item, SpeechStreamChunk):
                    mp3 = item.audio_bytes  # MP3 by default
                elif isinstance(item, SpeechStreamDone):
                    print(f"Done: {item.duration_s}s, format={item.format}")
            ```
        """
        json_body: dict = {
            "model": model,
            "input": input,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "stream": True,
        }
        if instructions is not None:
            json_body["instructions"] = instructions

        logger.debug(
            "Speech stream: model=%s, voice=%s, format=%s, input_len=%d",
            model, voice, response_format, len(input),
        )

        with handle_api_errors():
            with self._http_client.stream("POST", "/v1/audio/speech", json=json_body) as response:
                response.raise_for_status()
                yield from _parse_sse_stream(response.iter_lines())


class AsyncAudioResource(AsyncBaseResource):
    """Audio tool (async) - STT transcription and TTS speech.

    Async version of AudioResource.

    Example:
        ```python
        from sdkrouter import AsyncSDKRouter, AudioModel

        client = AsyncSDKRouter(api_key="your-api-key")

        result = await client.audio.transcribe(audio_bytes, model=AudioModel.cheap())
        print(result.text)

        response = await client.audio.speech(input="Hello!", voice="nova")
        Path("output.mp3").write_bytes(response.audio_bytes)
        ```
    """

    def __init__(self, config: "SDKConfig"):
        super().__init__(config, use_audio_url=True)

    @async_api_error_handler
    async def transcribe(
        self,
        file: bytes | str | Path,
        *,
        model: str = "whisper-1",
        language: str | None = None,
        response_format: TranscriptionResponseFormat = "json",
        temperature: float = 0,
        filename: str | None = None,
    ) -> TranscriptionResponse | VerboseTranscriptionResponse | str:
        """
        Transcribe audio to text (async).

        Args:
            file: Audio data as bytes, file path string, or Path object.
            model: STT model or tier alias ("@cheap", "@quality").
            language: ISO 639-1 language code. Optional.
            response_format: Output format (json, verbose_json, text, srt, vtt).
            temperature: Sampling temperature (0 to 1).
            filename: Filename hint for the uploaded audio.

        Returns:
            TranscriptionResponse, VerboseTranscriptionResponse, or str.
        """
        file_bytes, resolved_filename = _resolve_file(file, filename)

        files = {
            "file": (resolved_filename, file_bytes, _guess_mime_type(resolved_filename)),
        }
        data: dict = {
            "model": model,
            "response_format": response_format,
            "temperature": str(temperature),
        }
        if language:
            data["language"] = language

        logger.debug(
            "Transcribe async: model=%s, format=%s, file=%s (%d bytes)",
            model, response_format, resolved_filename, len(file_bytes),
        )

        response = await self._http_client.post(
            "/v1/audio/transcriptions",
            data=data,
            files=files,
        )
        response.raise_for_status()

        if response_format in ("text", "srt", "vtt"):
            return response.text
        elif response_format == "verbose_json":
            return VerboseTranscriptionResponse.model_validate(response.json())
        else:
            return TranscriptionResponse.model_validate(response.json())

    @async_api_error_handler
    async def speech(
        self,
        input: str,
        *,
        model: str = "tts-1",
        voice: str = "nova",
        response_format: TTSResponseFormat = "mp3",
        speed: float = 1.0,
        instructions: str | None = None,
    ) -> SpeechResponse:
        """
        Generate speech from text (async).

        Returns a SpeechResponse containing base64 audio and per-frame
        analysis metadata for visualization.

        Args:
            input: Text to synthesize (max 4096 characters).
            model: TTS model or tier alias.
            voice: Voice identifier. Default: "nova"
            response_format: Audio format. Default: "mp3"
            speed: Playback speed (0.25 to 4.0).
            instructions: Custom voice instructions.

        Returns:
            SpeechResponse with .audio_bytes property and .analysis data.
        """
        json_body: dict = {
            "model": model,
            "input": input,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }
        if instructions is not None:
            json_body["instructions"] = instructions

        logger.debug(
            "Speech async: model=%s, voice=%s, format=%s",
            model, voice, response_format,
        )

        response = await self._http_client.post(
            "/v1/audio/speech",
            json=json_body,
        )
        response.raise_for_status()
        return SpeechResponse.model_validate(response.json())

    async def speech_stream(
        self,
        input: str,
        *,
        model: str = "tts-1",
        voice: str = "nova",
        response_format: TTSResponseFormat = "mp3",
        speed: float = 1.0,
        instructions: str | None = None,
    ) -> AsyncIterator[SpeechStreamChunk | SpeechStreamDone]:
        """
        Generate speech from text with SSE streaming (async).

        Streams audio chunks with real-time analysis frames.
        Audio format defaults to MP3; set response_format="pcm" for raw PCM.
        The final yielded item is a SpeechStreamDone with summary info.

        Args:
            input: Text to synthesize (max 4096 characters).
            model: TTS model or tier alias.
            voice: Voice identifier. Default: "nova"
            response_format: Audio format for chunks: "mp3" (default) or "pcm".
            speed: Playback speed (0.25 to 4.0). Default: 1.0
            instructions: Custom voice instructions (for gpt-4o-mini-tts).

        Yields:
            SpeechStreamChunk for each audio chunk, then SpeechStreamDone.
        """
        json_body: dict = {
            "model": model,
            "input": input,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "stream": True,
        }
        if instructions is not None:
            json_body["instructions"] = instructions

        logger.debug(
            "Speech stream async: model=%s, voice=%s, format=%s, input_len=%d",
            model, voice, response_format, len(input),
        )

        async with self._http_client.stream("POST", "/v1/audio/speech", json=json_body) as response:
            response.raise_for_status()
            async for item in _parse_sse_stream_async(response.aiter_lines()):
                yield item


def _parse_sse_stream(
    lines: Iterator[str],
) -> Iterator[SpeechStreamChunk | SpeechStreamDone]:
    """Parse SSE text/event-stream lines into typed objects."""
    event_type: str | None = None
    for line in lines:
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            if event_type == "chunk":
                yield SpeechStreamChunk.model_validate_json(data_str)
            elif event_type == "done":
                yield SpeechStreamDone.model_validate_json(data_str)
            event_type = None
        elif line == "":
            # Empty line = end of SSE event block
            event_type = None


async def _parse_sse_stream_async(
    lines: AsyncIterator[str],
) -> AsyncIterator[SpeechStreamChunk | SpeechStreamDone]:
    """Parse SSE text/event-stream lines into typed objects (async)."""
    event_type: str | None = None
    async for line in lines:
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            if event_type == "chunk":
                yield SpeechStreamChunk.model_validate_json(data_str)
            elif event_type == "done":
                yield SpeechStreamDone.model_validate_json(data_str)
            event_type = None
        elif line == "":
            event_type = None


__all__ = [
    "AudioResource",
    "AsyncAudioResource",
]
