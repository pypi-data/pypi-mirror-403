"""Parsed chat completion types for structured output."""

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

ContentType = TypeVar("ContentType")


@dataclass
class ParsedMessage(Generic[ContentType]):
    """Message with parsed content from structured output."""

    role: str
    content: Optional[str] = None
    parsed: Optional[ContentType] = None
    refusal: Optional[str] = None
    tool_calls: Optional[list[Any]] = None
    function_call: Optional[Any] = None

    @classmethod
    def from_message(
        cls,
        message: Any,
        parsed_content: Optional[ContentType] = None,
    ) -> "ParsedMessage[ContentType]":
        """Create ParsedMessage from raw ChatCompletionMessage."""
        return cls(
            role=getattr(message, "role", "assistant"),
            content=getattr(message, "content", None),
            parsed=parsed_content,
            refusal=getattr(message, "refusal", None),
            tool_calls=getattr(message, "tool_calls", None),
            function_call=getattr(message, "function_call", None),
        )


@dataclass
class ParsedChoice(Generic[ContentType]):
    """Choice with parsed message."""

    index: int
    message: ParsedMessage[ContentType]
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None

    @classmethod
    def from_choice(
        cls,
        choice: Any,
        parsed_content: Optional[ContentType] = None,
    ) -> "ParsedChoice[ContentType]":
        """Create ParsedChoice from raw Choice."""
        return cls(
            index=getattr(choice, "index", 0),
            message=ParsedMessage.from_message(
                getattr(choice, "message", None),
                parsed_content=parsed_content,
            ),
            finish_reason=getattr(choice, "finish_reason", None),
            logprobs=getattr(choice, "logprobs", None),
        )


@dataclass
class ParsedChatCompletion(Generic[ContentType]):
    """ChatCompletion with parsed content from structured output."""

    id: str
    choices: list[ParsedChoice[ContentType]]
    created: int
    model: str
    object: str = "chat.completion"
    system_fingerprint: Optional[str] = None
    usage: Optional[Any] = None
    service_tier: Optional[str] = None

    @classmethod
    def from_completion(
        cls,
        completion: Any,
        parsed_choices: list[ParsedChoice[ContentType]],
    ) -> "ParsedChatCompletion[ContentType]":
        """Create ParsedChatCompletion from raw ChatCompletion."""
        return cls(
            id=getattr(completion, "id", ""),
            choices=parsed_choices,
            created=getattr(completion, "created", 0),
            model=getattr(completion, "model", ""),
            object=getattr(completion, "object", "chat.completion"),
            system_fingerprint=getattr(completion, "system_fingerprint", None),
            usage=getattr(completion, "usage", None),
            service_tier=getattr(completion, "service_tier", None),
        )


__all__ = [
    "ContentType",
    "ParsedMessage",
    "ParsedChoice",
    "ParsedChatCompletion",
]
