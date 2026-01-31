"""Audio model alias builder with IDE autocomplete.

Build audio model alias strings for STT/TTS tier-based routing.

Audio tiers: cheap, quality, fast, balanced
Audio modifiers: +streaming, +instructions

Usage::

    from sdkrouter import AudioModel

    AudioModel.cheap()                          # "@cheap"
    AudioModel.quality(streaming=True)          # "@quality+streaming"
    AudioModel.fast(instructions=True)          # "@fast+instructions"

    # Works with audio resource
    result = client.audio.transcribe(
        file=audio_bytes,
        model=AudioModel.cheap(),
    )

    audio = client.audio.speech(
        input="Hello world",
        model=AudioModel.quality(streaming=True),
        voice="nova",
    )
"""


class AudioModel:
    """Build audio model alias strings with IDE autocomplete.

    Instead of memorizing ``"@quality+streaming"``, use::

        AudioModel.quality(streaming=True)

    Each method returns a plain ``str`` that works directly with
    ``model=`` parameters on audio methods.

    Audio-specific tiers:
        - cheap: Lowest cost transcription/synthesis
        - quality: Best quality output
        - fast: Lowest latency
        - balanced: Best quality/price ratio

    Audio-specific modifiers:
        - streaming: Model supports streaming output
        - instructions: Model supports custom voice instructions (TTS)
    """

    @staticmethod
    def _build(
        tier: str,
        *,
        streaming: bool = False,
        instructions: bool = False,
    ) -> str:
        parts = [tier]
        if streaming:
            parts.append("streaming")
        if instructions:
            parts.append("instructions")
        return "@" + "+".join(parts)

    # -- Tier methods (full typed signatures for IDE autocomplete) --

    @staticmethod
    def cheap(
        *,
        streaming: bool = False,
        instructions: bool = False,
    ) -> str:
        """Cheapest available audio model."""
        return AudioModel._build(
            "cheap", streaming=streaming, instructions=instructions,
        )

    @staticmethod
    def quality(
        *,
        streaming: bool = False,
        instructions: bool = False,
    ) -> str:
        """Highest quality audio model."""
        return AudioModel._build(
            "quality", streaming=streaming, instructions=instructions,
        )

    @staticmethod
    def fast(
        *,
        streaming: bool = False,
        instructions: bool = False,
    ) -> str:
        """Lowest latency audio model."""
        return AudioModel._build(
            "fast", streaming=streaming, instructions=instructions,
        )

    @staticmethod
    def balanced(
        *,
        streaming: bool = False,
        instructions: bool = False,
    ) -> str:
        """Best quality/price ratio audio model."""
        return AudioModel._build(
            "balanced", streaming=streaming, instructions=instructions,
        )

    @staticmethod
    def alias(preset: str, *modifiers: str) -> str:
        """Build alias from raw strings (escape hatch).

        Example::

            AudioModel.alias("cheap", "streaming")  # "@cheap+streaming"
        """
        return "@" + "+".join([preset, *modifiers])
