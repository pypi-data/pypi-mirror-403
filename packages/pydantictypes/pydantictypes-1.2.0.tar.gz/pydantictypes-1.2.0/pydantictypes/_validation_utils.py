"""Internal validation utilities for pydantictypes."""

from __future__ import annotations

from typing import Any


# Reason: The argument of pydantic type
def validate_optional_string_type(value: Any) -> str | None:  # noqa: ANN401
    """Validate and normalize optional string values.

    This helper function provides common validation logic for optional string validators.
    It handles None values, type checking, and empty string conversion.

    Args:
        value: The value to validate.

    Returns:
        The validated string or None if the value is None or empty string.

    Raises:
        TypeError: If value is not None or a string.
    """
    # Handle None before type check
    if value is None:
        return None

    if not isinstance(value, str):
        msg = f"String required. Value is {value}. Type is {type(value)}."
        raise TypeError(msg)

    if value == "":
        return None

    return value
