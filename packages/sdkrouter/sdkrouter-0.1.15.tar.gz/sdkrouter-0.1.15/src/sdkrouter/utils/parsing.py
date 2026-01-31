"""Utilities for structured output parsing with Pydantic models."""

from typing import Any, Type, TypeVar

from pydantic import BaseModel

ResponseFormatT = TypeVar("ResponseFormatT", bound=BaseModel)


def to_strict_json_schema(model: Type[BaseModel]) -> dict[str, Any]:
    """
    Convert Pydantic model to strict JSON Schema for OpenAI API.

    Strict mode requires:
    - additionalProperties: false at all levels
    - All properties must be in required array

    Args:
        model: Pydantic model class

    Returns:
        JSON Schema dict compatible with OpenAI strict mode
    """
    schema = model.model_json_schema()
    return _ensure_strict_schema(schema)


def _ensure_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Make schema strict (additionalProperties: false, all required).

    Recursively processes nested objects and $defs.

    Args:
        schema: JSON Schema dict

    Returns:
        Modified schema with strict mode settings
    """
    schema = schema.copy()

    # Process $defs (referenced schemas)
    if "$defs" in schema:
        new_defs = {}
        for name, definition in schema["$defs"].items():
            new_defs[name] = _ensure_strict_schema(definition)
        schema["$defs"] = new_defs

    # Set additionalProperties: false for objects
    if schema.get("type") == "object":
        schema["additionalProperties"] = False

        # Make all properties required
        if "properties" in schema:
            schema["required"] = list(schema["properties"].keys())

            # Process nested properties
            new_props = {}
            for prop_name, prop_schema in schema["properties"].items():
                new_props[prop_name] = _ensure_strict_schema(prop_schema)
            schema["properties"] = new_props

    # Process array items
    if schema.get("type") == "array" and "items" in schema:
        schema["items"] = _ensure_strict_schema(schema["items"])

    # Process anyOf/oneOf/allOf
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            schema[key] = [_ensure_strict_schema(item) for item in schema[key]]

    return schema


def type_to_response_format(response_format: Type[BaseModel]) -> dict[str, Any]:
    """
    Convert Pydantic model to OpenAI response_format parameter.

    Args:
        response_format: Pydantic model class for response parsing

    Returns:
        Dict compatible with OpenAI response_format parameter

    Example:
        >>> class Answer(BaseModel):
        ...     text: str
        ...     confidence: float
        >>> fmt = type_to_response_format(Answer)
        >>> fmt["type"]
        'json_schema'
        >>> fmt["json_schema"]["strict"]
        True
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": response_format.__name__,
            "schema": to_strict_json_schema(response_format),
            "strict": True,
        },
    }


__all__ = [
    "ResponseFormatT",
    "to_strict_json_schema",
    "type_to_response_format",
]
