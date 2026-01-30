"""Custom data types."""

from __future__ import annotations

from typing import Optional

from pydantic import BeforeValidator

from pydantictypes.abstract_string_to_optional_int import OptionalIntegerMustBeFromStr

# Reason: To use raw typing imports pylint: disable=duplicate-code
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

__all__ = [
    "ConstrainedStringToOptionalInt",
    "constringtooptionalint",
]


# Reason: Constraint parameters follow Pydantic specification (gt, ge, lt, le, multiple_of)
def constringtooptionalint(  # noqa: PLR0913 pylint: disable=too-many-arguments
    *,
    # Reason: Kept for backward compatibility but no longer used in Pydantic v2
    strict: bool | None = None,  # noqa: ARG001  # pylint: disable=unused-argument
    gt: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    le: int | None = None,
    multiple_of: int | None = None,
) -> type[int | None]:
    """A wrapper around `int` that allows for additional constraints.

    Args:
        strict: Whether to validate the integer in strict mode. Defaults to `None`.
            Note: This parameter is kept for backward compatibility but is no longer used.
        gt: The value must be greater than this.
        ge: The value must be greater than or equal to this.
        lt: The value must be less than this.
        le: The value must be less than or equal to this.
        multiple_of: The value must be a multiple of this.

    Returns:
        The wrapped integer type.
    """
    # Create validator with constraints - constraints are validated in the validator itself
    # Note: We don't include annotated_types metadata because Pydantic would try to apply
    # those constraints AFTER our BeforeValidator, which fails when validator returns None
    validator = OptionalIntegerMustBeFromStr(
        int,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
    )
    return Annotated[Optional[int], BeforeValidator(validator.validate)]  # type: ignore[return-value]


# Basic type without constraints (for simple string to optional int conversion)
ConstrainedStringToOptionalInt = Annotated[
    Optional[int],
    BeforeValidator(OptionalIntegerMustBeFromStr(int).validate),
]
