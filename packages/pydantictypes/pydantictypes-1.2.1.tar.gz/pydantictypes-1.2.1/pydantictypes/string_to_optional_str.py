"""Custom data type to convert string to optional str with constraints."""

from __future__ import annotations

import re
from typing import Any
from typing import Optional
from typing import Pattern

from pydantic import BeforeValidator

from pydantictypes._validation_utils import validate_optional_string_type

# Reason: To use raw typing imports
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "StringToOptionalStr",
    "constringtooptionalstr",
]


class StringToOptionalStrValidator:
    """Validator for optional string with constraints."""

    # Reason: Following Pydantic specification.
    def __init__(  # noqa: PLR0913 pylint: disable=too-many-arguments
        self,
        *,
        strip_whitespace: bool = False,
        to_lower: bool = False,
        strict: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
        curtail_length: int | None = None,
        regex: str | Pattern[str] | None = None,
    ) -> None:
        self.strip_whitespace = strip_whitespace
        self.to_lower = to_lower
        self.strict = strict
        self.min_length = min_length
        self.max_length = max_length
        self.curtail_length = curtail_length
        self.regex = re.compile(regex) if isinstance(regex, str) else regex

    def _apply_transformations(self, value: str) -> str:
        """Apply transformations to the string.

        Args:
            value: The string to transform.

        Returns:
            The transformed string.
        """
        if self.strip_whitespace:
            value = value.strip()

        if self.to_lower:
            value = value.lower()

        if self.curtail_length is not None:
            value = value[: self.curtail_length]

        return value

    def _validate_length(self, value: str) -> None:
        """Validate string length constraints.

        Args:
            value: The string to validate.

        Raises:
            ValueError: If the string does not meet length constraints.
        """
        length = len(value)

        if self.min_length is not None and length < self.min_length:
            msg = f"String length must be at least {self.min_length}"
            raise ValueError(msg)

        if self.max_length is not None and length > self.max_length:
            msg = f"String length must be at most {self.max_length}"
            raise ValueError(msg)

    def _validate_pattern(self, value: str) -> None:
        """Validate string against regex pattern.

        Args:
            value: The string to validate.

        Raises:
            ValueError: If the string does not match the pattern.
        """
        if self.regex is not None and not self.regex.match(value):
            msg = f"String does not match pattern {self.regex.pattern}"
            raise ValueError(msg)

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> str | None:  # noqa: ANN401
        """Validate optional string with constraints.

        Args:
            value: The value to validate.

        Returns:
            The validated and processed string or None if empty.

        Raises:
            TypeError: If value is not a string.
            ValueError: If value does not meet the constraints.
        """
        if value is None:
            msg = f"String required. Value is {value}. Type is {type(value)}."
            raise TypeError(msg)

        validated = validate_optional_string_type(value)
        if validated is None:
            return None

        validated = self._apply_transformations(validated)
        self._validate_length(validated)
        self._validate_pattern(validated)

        return validated


StringToOptionalStr = Annotated[
    Optional[str],
    BeforeValidator(StringToOptionalStrValidator().validate),
]


# Reason: Followed Pydantic specification.
def constringtooptionalstr(  # noqa: PLR0913 pylint: disable=too-many-arguments
    *,
    strip_whitespace: bool = False,
    to_lower: bool = False,
    strict: bool = False,
    min_length: int | None = None,
    max_length: int | None = None,
    curtail_length: int | None = None,
    regex: str | None = None,
) -> type[str | None]:
    """A wrapper around `Optional[str]` that allows for additional constraints.

    Args:
        strip_whitespace: Whether to strip leading and trailing whitespace. Defaults to False.
        to_lower: Whether to convert the string to lowercase. Defaults to False.
        strict: Whether to validate in strict mode (currently unused). Defaults to False.
        min_length: The minimum length of the string.
        max_length: The maximum length of the string.
        curtail_length: The maximum length to truncate the string to.
        regex: A regular expression pattern the string must match.

    Returns:
        The wrapped optional string type.
    """
    validator = StringToOptionalStrValidator(
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        strict=strict,
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
        regex=regex,
    )
    before_validator = BeforeValidator(validator.validate)
    return Annotated[Optional[str], before_validator]  # type: ignore[return-value]
