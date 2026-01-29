"""Custom data types for half-width character validation."""

from __future__ import annotations

import unicodedata
from typing import Any
from typing import Optional

from pydantic import BeforeValidator

from pydantictypes._validation_utils import validate_optional_string_type

# Reason: To use raw typing imports
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "HalfWidthString",
    "OptionalHalfWidthString",
]


def _check_half_width_characters(value: str) -> None:
    """Check if string contains only half-width characters.

    Args:
        value: The string to check.

    Raises:
        ValueError: If string contains full-width or ambiguous characters.
    """
    for char in value:
        width = unicodedata.east_asian_width(char)
        # Reject Wide, Fullwidth, and Ambiguous character widths
        if width in ["W", "F", "A"]:
            msg = "Must contain only half-width characters."
            raise ValueError(msg)


class HalfWidthValidator:
    """Validator to check that string contains only half-width characters."""

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> str:  # noqa: ANN401
        """Validate that string contains only half-width characters.

        Args:
            value: The value to validate.

        Returns:
            The validated string.

        Raises:
            TypeError: If value is not a string.
            ValueError: If string contains full-width or ambiguous characters.
        """
        if not isinstance(value, str):
            msg = f"String required. Value is {value}. Type is {type(value)}."
            raise TypeError(msg)

        _check_half_width_characters(value)

        return value


class OptionalHalfWidthValidator:
    """Validator to check that optional string contains only half-width characters."""

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> str | None:  # noqa: ANN401
        """Validate that optional string contains only half-width characters.

        Args:
            value: The value to validate.

        Returns:
            The validated string or None.

        Raises:
            TypeError: If value is not a string.
            ValueError: If string contains full-width or ambiguous characters.
        """
        validated = validate_optional_string_type(value)
        if validated is None:
            return None

        _check_half_width_characters(validated)

        return validated


HalfWidthString = Annotated[
    str,
    BeforeValidator(HalfWidthValidator().validate),
]

OptionalHalfWidthString = Annotated[
    Optional[str],
    BeforeValidator(OptionalHalfWidthValidator().validate),
]
