"""Custom data types for string length validation."""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Optional

from pydantic import BeforeValidator

from pydantictypes._validation_utils import validate_optional_string_type

# Reason: To use raw typing imports
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "ConstrainedOptionalStringWithLength",
    "ConstrainedStringWithLength",
    "constrained_optional_string",
    "constrained_string",
]


def _validate_length_constraint(
    *,
    length: int,
    constraint_value: int | None,
    condition: Callable[[int, int], bool],
    error_message: str,
) -> None:
    """Validate a single length constraint.

    Args:
        length: The actual string length.
        constraint_value: The constraint value to check against (None to skip validation).
        condition: How to compare length and constraint_value.
        error_message: The error message to raise if validation fails.

    Raises:
        ValueError: If the constraint is violated.
    """
    if constraint_value is None:
        return

    if condition(length, constraint_value):
        msg = f"String length must be {error_message}"
        raise ValueError(msg)


def _check_string_length(
    value: str,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    equal_to: int | None = None,
) -> None:
    """Check if string meets length constraints.

    Args:
        value: The string to check.
        min_length: The minimum length allowed.
        max_length: The maximum length allowed.
        equal_to: The exact length required.

    Raises:
        ValueError: If string does not meet length constraints.
    """
    length = len(value)

    _validate_length_constraint(
        length=length,
        constraint_value=equal_to,
        condition=lambda a, b: a != b,
        error_message=f"equal to {equal_to}",
    )

    _validate_length_constraint(
        length=length,
        constraint_value=min_length,
        condition=lambda a, b: a < b,
        error_message=f"at least {min_length}",
    )

    _validate_length_constraint(
        length=length,
        constraint_value=max_length,
        condition=lambda a, b: a > b,
        error_message=f"at most {max_length}",
    )


class StringLengthValidator:
    """Validator for string length constraints."""

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        equal_to: int | None = None,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.equal_to = equal_to

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> str:  # noqa: ANN401
        """Validate string length."""
        if not isinstance(value, str):
            msg = f"String required. Value is {value}. Type is {type(value)}."
            raise TypeError(msg)

        _check_string_length(
            value,
            min_length=self.min_length,
            max_length=self.max_length,
            equal_to=self.equal_to,
        )

        return value


class OptionalStringLengthValidator:
    """Validator for optional string length constraints."""

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        equal_to: int | None = None,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.equal_to = equal_to

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> str | None:  # noqa: ANN401
        """Validate optional string length."""
        validated = validate_optional_string_type(value)
        if validated is None:
            return None

        _check_string_length(
            validated,
            min_length=self.min_length,
            max_length=self.max_length,
            equal_to=self.equal_to,
        )

        return validated


# Basic constrained type without parameters
ConstrainedStringWithLength = Annotated[
    str,
    BeforeValidator(StringLengthValidator().validate),
]

# Optional variant
ConstrainedOptionalStringWithLength = Annotated[
    Optional[str],
    BeforeValidator(OptionalStringLengthValidator().validate),
]


# Reason: Followed Pydantic specification.
def constrained_string(
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    equal_to: int | None = None,
) -> type[str]:
    """A wrapper around `str` that allows for length constraints.

    Args:
        min_length: The minimum length of the string.
        max_length: The maximum length of the string.
        equal_to: The exact length the string must be.

    Returns:
        The wrapped string type.
    """
    validator = StringLengthValidator(min_length=min_length, max_length=max_length, equal_to=equal_to)
    before_validator = BeforeValidator(validator.validate)
    return Annotated[str, before_validator]  # type: ignore[return-value]


# Reason: Followed Pydantic specification.
def constrained_optional_string(
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    equal_to: int | None = None,
) -> type[str | None]:
    """A wrapper around `Optional[str]` that allows for length constraints.

    Args:
        min_length: The minimum length of the string.
        max_length: The maximum length of the string.
        equal_to: The exact length the string must be.

    Returns:
        The wrapped optional string type.
    """
    validator = OptionalStringLengthValidator(min_length=min_length, max_length=max_length, equal_to=equal_to)
    before_validator = BeforeValidator(validator.validate)
    return Annotated[Optional[str], before_validator]  # type: ignore[return-value]
