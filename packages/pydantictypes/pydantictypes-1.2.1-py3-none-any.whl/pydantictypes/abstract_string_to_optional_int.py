"""Custom data type to convert string to optional int."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import annotated_types

from pydantictypes._validation_utils import validate_optional_string_type

if TYPE_CHECKING:
    from collections.abc import Callable


def _check_gt_constraint(value: int, gt: int | None) -> None:
    if gt is not None and not value > gt:
        msg = f"Input should be greater than {gt}"
        raise ValueError(msg)


def _check_ge_constraint(value: int, ge: int | None) -> None:
    if ge is not None and not value >= ge:
        msg = f"Input should be greater than or equal to {ge}"
        raise ValueError(msg)


def _check_lt_constraint(value: int, lt: int | None) -> None:
    if lt is not None and not value < lt:
        msg = f"Input should be less than {lt}"
        raise ValueError(msg)


def _check_le_constraint(value: int, le: int | None) -> None:
    if le is not None and not value <= le:
        msg = f"Input should be less than or equal to {le}"
        raise ValueError(msg)


def _check_multiple_of_constraint(value: int, multiple_of: int | None) -> None:
    if multiple_of is not None and value % multiple_of != 0:
        msg = f"Input should be a multiple of {multiple_of}"
        raise ValueError(msg)


# Reason: Constraint parameters follow Pydantic specification (gt, ge, lt, le, multiple_of)
def _check_numeric_constraints(  # noqa: PLR0913 pylint: disable=too-many-arguments
    value: int,
    *,
    gt: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    le: int | None = None,
    multiple_of: int | None = None,
) -> None:
    """Check if integer meets numeric constraints.

    Args:
        value: The integer to check.
        gt: The value must be greater than this.
        ge: The value must be greater than or equal to this.
        lt: The value must be less than this.
        le: The value must be less than or equal to this.
        multiple_of: The value must be a multiple of this.

    Raises:
        ValueError: If the value does not meet the constraints.
    """
    _check_gt_constraint(value, gt)
    _check_ge_constraint(value, ge)
    _check_lt_constraint(value, lt)
    _check_le_constraint(value, le)
    _check_multiple_of_constraint(value, multiple_of)


class OptionalIntegerMustBeFromStr:
    """Validator to convert string to optional int with numeric constraints."""

    # Reason: Constraint parameters follow Pydantic specification
    def __init__(  # noqa: PLR0913 pylint: disable=too-many-arguments
        self,
        string_to_int: Callable[[str], int],
        *,
        gt: int | None = None,
        ge: int | None = None,
        lt: int | None = None,
        le: int | None = None,
        multiple_of: int | None = None,
    ) -> None:
        self.string_to_int = string_to_int
        self.gt = gt
        self.ge = ge
        self.lt = lt
        self.le = le
        self.multiple_of = multiple_of

    # Reason: The argument of pydantic type
    def validate(self, value: Any) -> int | None:  # noqa: ANN401
        """Validate and convert string to optional int with constraint checking.

        Args:
            value: The value to validate.

        Returns:
            The converted integer or None if value is None or empty string.

        Raises:
            TypeError: If value is not None or a string.
            ValueError: If the value does not meet the constraints.
        """
        validated = validate_optional_string_type(value)
        if validated is None:
            return None
        result = self.string_to_int(validated)
        _check_numeric_constraints(
            result,
            gt=self.gt,
            ge=self.ge,
            lt=self.lt,
            le=self.le,
            multiple_of=self.multiple_of,
        )
        return result


# Reason: Constraint parameters follow Pydantic specification (gt, ge, lt, le, multiple_of)
def abstract_constringtooptionalint(  # noqa: PLR0913 pylint: disable=too-many-arguments
    *,
    # Reason: Kept for backward compatibility but no longer used in Pydantic v2
    strict: bool | None = None,  # noqa: ARG001  # pylint: disable=unused-argument
    gt: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    le: int | None = None,
    multiple_of: int | None = None,
) -> list[Any]:
    """A wrapper around `int` that allows for additional constraints.

    Note: The strict parameter is kept for backward compatibility but is no longer used.
    Constraints are now validated directly in the OptionalIntegerMustBeFromStr class.
    """
    return [
        annotated_types.Interval(gt=gt, ge=ge, lt=lt, le=le),
        annotated_types.MultipleOf(multiple_of) if multiple_of is not None else None,
    ]
