# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Common validators for resource variant references.

This module provides reusable validation functions for inputs that reference
resources by name/variant, either as strings, tuples, or HasNameVariant objects.
"""

from typing import Any, Optional, Tuple, Union

from ..core import HasNameVariant

__all__ = [
    "validate_string_or_resource",
    "validate_tuple_or_resource",
    "validate_name_variant_tuple",
    "normalize_variant",
]


def validate_string_or_resource(
    value: Any,
    field_name: str = "value",
    allow_none: bool = False,
) -> Union[str, HasNameVariant, None]:
    """
    Validate that a value is either a string name or a HasNameVariant resource.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
        allow_none: Whether None is a valid value.

    Returns:
        The validated value (stripped string or HasNameVariant object).

    Raises:
        ValueError: If the value is invalid.
    """
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"{field_name} cannot be None")

    if isinstance(value, tuple):
        raise ValueError(
            f"Tuples are not supported for {field_name}. "
            f"Use a string name with variant parameter, or a resource object."
        )

    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} name cannot be empty")
        return value

    if isinstance(value, HasNameVariant):
        return value

    raise ValueError(
        f"{field_name} must be a string name or an object implementing HasNameVariant"
    )


def validate_name_variant_tuple(
    value: Any,
    field_name: str = "value",
) -> Tuple[str, str]:
    """
    Validate that a value is a valid (name, variant) tuple.

    Args:
        value: The tuple to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated (name, variant) tuple with stripped strings.

    Raises:
        ValueError: If the tuple is invalid.
    """
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")

    if len(value) != 2:
        raise ValueError(f"{field_name} tuple must be ('name', 'variant')")

    name = str(value[0]).strip()
    variant = str(value[1]).strip()

    if not name:
        raise ValueError(f"{field_name} name cannot be empty")
    if not variant:
        raise ValueError(f"{field_name} variant cannot be empty")

    return (name, variant)


def validate_tuple_or_resource(
    value: Any,
    field_name: str = "value",
    allow_none: bool = False,
) -> Union[Tuple[str, str], HasNameVariant, None]:
    """
    Validate that a value is either a (name, variant) tuple or a HasNameVariant resource.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
        allow_none: Whether None is a valid value.

    Returns:
        The validated value (tuple or HasNameVariant object).

    Raises:
        ValueError: If the value is invalid.
    """
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"{field_name} cannot be None")

    if isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a ('name', 'variant') tuple or a resource "
            f"implementing name_variant()"
        )

    if isinstance(value, tuple):
        return validate_name_variant_tuple(value, field_name)

    if isinstance(value, HasNameVariant):
        return value

    raise ValueError(
        f"{field_name} must be None, a ('name', 'variant') tuple, "
        f"or an object implementing name_variant()"
    )


def normalize_variant(
    value: Any,
    field_name: str = "variant",
) -> Optional[str]:
    """
    Normalize a variant string value.

    Args:
        value: The variant value to normalize.
        field_name: Name of the field for error messages.

    Returns:
        The normalized variant string, or None if value is None.

    Raises:
        ValueError: If the variant is empty after stripping.
    """
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    return value
