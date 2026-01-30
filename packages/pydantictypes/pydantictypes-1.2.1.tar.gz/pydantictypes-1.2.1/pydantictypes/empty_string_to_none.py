"""Custom data type to validate empty string to None."""

from __future__ import annotations

from typing import Any

from pydantic import BeforeValidator

# Reason: To use raw typing imports
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "EmptyStringToNone",
]


class EmptyStringToNoneValidator:
    """Validator that only accepts empty strings and converts them to None."""

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> None:  # noqa: ANN401
        """Validate that value is an empty string and convert to None.

        Args:
            value: The value to validate.

        Returns:
            None if value is an empty string.

        Raises:
            TypeError: If value is not a string.
            ValueError: If value is not an empty string.
        """
        if not isinstance(value, str):
            msg = f"String required. Value is {value}. Type is {type(value)}."
            raise TypeError(msg)
        if value == "":
            return
        msg = "Value must be an empty string ''"
        raise ValueError(msg)


EmptyStringToNone = Annotated[
    None,
    BeforeValidator(EmptyStringToNoneValidator().validate),
]
