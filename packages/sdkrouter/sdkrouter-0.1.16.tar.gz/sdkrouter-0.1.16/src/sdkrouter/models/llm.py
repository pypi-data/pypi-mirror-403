"""Model alias builder with IDE autocomplete.

Build model alias strings from typed parameters instead of memorizing raw syntax.

Usage::

    from sdkrouter import Model

    Model.cheap()                       # "@cheap"
    Model.smart(vision=True, code=True) # "@smart+vision+code"

    # Works directly with client
    response = client.chat.completions.create(
        model=Model.balanced(tools=True),
        messages=[...],
    )
"""

# Re-export enums under clean names
from .._api.generated.models.enums import PresetSlug as Tier
from .._api.generated.models.enums import CategorySlug as Category
from .._api.generated.models.enums import (
    CapabilitiesListResponseCapabilitiesItems as Capability,
)


class Model:
    """Build model alias strings with IDE autocomplete.

    Instead of memorizing ``"@cheap+vision+code"``, use::

        Model.cheap(vision=True, code=True)

    Each method returns a plain ``str`` that works directly with
    ``model=`` parameters.
    """

    @staticmethod
    def _build(
        tier: str,
        *,
        # Capabilities
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        # Categories
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        parts = [tier]
        # Capabilities
        if vision:
            parts.append("vision")
        if tools:
            parts.append("tools")
        if json:
            parts.append("json")
        if streaming:
            parts.append("streaming")
        if long:
            parts.append("long")
        # Categories
        if code:
            parts.append("code")
        if reasoning:
            parts.append("reasoning")
        if creative:
            parts.append("creative")
        if agents:
            parts.append("agents")
        if analysis:
            parts.append("analysis")
        if chat:
            parts.append("chat")
        return "@" + "+".join(parts)

    # -- Tier methods (full typed signatures for IDE autocomplete) --

    @staticmethod
    def cheap(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Cheapest available model."""
        return Model._build(
            "cheap", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def budget(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Budget-friendly with decent quality."""
        return Model._build(
            "budget", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def standard(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Standard tier."""
        return Model._build(
            "standard", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def balanced(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Best quality/price ratio."""
        return Model._build(
            "balanced", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def smart(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Highest quality model."""
        return Model._build(
            "smart", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def fast(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Lowest latency model."""
        return Model._build(
            "fast", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def premium(
        *,
        vision: bool = False,
        tools: bool = False,
        json: bool = False,
        streaming: bool = False,
        long: bool = False,
        code: bool = False,
        reasoning: bool = False,
        creative: bool = False,
        agents: bool = False,
        analysis: bool = False,
        chat: bool = False,
    ) -> str:
        """Top-tier premium model."""
        return Model._build(
            "premium", vision=vision, tools=tools, json=json,
            streaming=streaming, long=long, code=code, reasoning=reasoning,
            creative=creative, agents=agents, analysis=analysis, chat=chat,
        )

    @staticmethod
    def alias(preset: str, *modifiers: str) -> str:
        """Build alias from raw strings (escape hatch).

        Example::

            Model.alias("cheap", "vision", "code")  # "@cheap+vision+code"
        """
        return "@" + "+".join([preset, *modifiers])
