"""Custom data type to convert string to optional bool."""

from __future__ import annotations

from enum import Flag
from typing import Any
from typing import ClassVar
from typing import Optional

from pydantic import BeforeValidator

# Reason: To use raw typing imports
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "StringToBoolean",
    "StringToOptionalBool",
]


class StringToBoolean(Flag):
    """Boolean representation with string serialization.

    This Flag enum represents boolean values that can be serialized to strings "1" (True) and "0" (False).
    """

    TRUE = True
    FALSE = False

    def __str__(self) -> str:
        """Convert to string representation.

        Returns:
            "1" for True, "0" for False.
        """
        return "1" if self.value else "0"


class StringToOptionalBoolValidator:
    """Validator to convert string to optional boolean."""

    # Mapping from string values to their boolean representations
    _VALUE_MAP: ClassVar[dict[str, StringToBoolean | None]] = {
        "1": StringToBoolean.TRUE,
        "0": StringToBoolean.FALSE,
        "": None,
    }

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> StringToBoolean | None:  # noqa: ANN401
        """Validate and convert string to optional boolean.

        Args:
            value: The value to validate (expected to be "1", "0", or "").

        Returns:
            StringToBoolean.TRUE if value is "1",
            StringToBoolean.FALSE if value is "0",
            None if value is "".

        Raises:
            TypeError: If value is not a string.
            ValueError: If value is not "1", "0", or "".
        """
        if not isinstance(value, str):
            msg = f"String required. Value is {value}. Type is {type(value)}."
            raise TypeError(msg)

        if value not in self._VALUE_MAP:
            msg = "Value must be '1', '0', or ''"
            raise ValueError(msg)

        return self._VALUE_MAP[value]


StringToOptionalBool = Annotated[
    Optional[StringToBoolean],
    BeforeValidator(StringToOptionalBoolValidator().validate),
]
