"""Serialization utilities for Simforge SDK.

This module provides serialization with type metadata preservation,
similar to superjson in JavaScript. Uses jsonpickle for handling
arbitrary Python objects including datetime, Decimal, UUID, sets,
custom classes, etc.
"""

from typing import Any, TypedDict

import jsonpickle


class SerializedValue(TypedDict, total=False):
    """Serialized value with JSON data and optional type metadata.

    Attributes:
        json: The JSON-serializable data
        meta: Type metadata for reconstructing special types (only present if needed)
    """

    json: Any
    meta: Any


def serialize_value(value: Any) -> SerializedValue:
    """Serialize a value using jsonpickle for type preservation.

    Handles arbitrary Python objects including:
    - datetime, date, time
    - Decimal, UUID
    - set, frozenset
    - bytes, bytearray
    - Custom classes
    - Pydantic models

    Args:
        value: Any Python value to serialize

    Returns:
        SerializedValue with 'json' field containing the data.
        If type metadata is needed for reconstruction, includes 'meta' field.

    Example:
        >>> from datetime import datetime
        >>> result = serialize_value(datetime(2024, 1, 15, 10, 30))
        >>> result['json']  # Contains the serialized datetime
        >>> result.get('meta')  # Contains type info if present
    """
    if value is None:
        return {"json": None}

    # For simple JSON-native types, no metadata needed
    if isinstance(value, (str, int, float, bool)):
        return {"json": value}

    # For dicts and lists of simple types, try plain JSON first
    if isinstance(value, (dict, list)):
        try:
            # Check if it's already JSON-serializable without special types
            import json

            json.dumps(value)
            return {"json": value}
        except (TypeError, ValueError):
            # Contains special types, use jsonpickle
            pass

    # Use jsonpickle for everything else
    try:
        # Encode with type information (unpicklable=True preserves type markers)
        encoded = jsonpickle.encode(value, unpicklable=True)
        # Parse back to get the JSON structure
        import json

        parsed = json.loads(encoded)

        # Check if jsonpickle added type markers
        if _has_type_markers(parsed):
            # Return with metadata indicating jsonpickle encoding
            return {"json": parsed, "meta": {"encoding": "jsonpickle"}}
        else:
            # No special types, return plain JSON
            return {"json": parsed}
    except Exception:
        # Fallback: try basic serialization
        try:
            if hasattr(value, "model_dump"):  # Pydantic v2
                return {"json": value.model_dump()}
            elif hasattr(value, "dict"):  # Pydantic v1
                return {"json": value.dict()}
            else:
                return {"json": str(value)}
        except Exception:
            return {"json": str(value)}


def deserialize_value(serialized: SerializedValue) -> Any:
    """Deserialize a value that was serialized with serialize_value.

    Args:
        serialized: A SerializedValue dict with 'json' and optional 'meta'

    Returns:
        The reconstructed Python value
    """
    json_data = serialized.get("json")
    meta = serialized.get("meta")

    if meta is None:
        # No metadata, return as-is
        return json_data

    if isinstance(meta, dict) and meta.get("encoding") == "jsonpickle":
        # Decode using jsonpickle
        import json

        encoded = json.dumps(json_data)
        return jsonpickle.decode(encoded)

    # Unknown metadata format, return raw JSON
    return json_data


def _has_type_markers(obj: Any) -> bool:
    """Check if a JSON structure contains jsonpickle type markers."""
    if isinstance(obj, dict):
        # Check for jsonpickle's type marker keys
        if "py/object" in obj or "py/type" in obj or "py/reduce" in obj:
            return True
        # Check nested values
        return any(_has_type_markers(v) for v in obj.values())
    elif isinstance(obj, list):
        return any(_has_type_markers(item) for item in obj)
    return False
