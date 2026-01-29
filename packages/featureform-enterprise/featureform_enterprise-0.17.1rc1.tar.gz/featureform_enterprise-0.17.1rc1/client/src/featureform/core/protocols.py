# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Protocol definitions for Featureform resources.

This module defines protocols (structural typing) for resources to enable
duck typing and reduce coupling.
"""

from typing import Protocol, Tuple, runtime_checkable

from ..enums import OperationType, ResourceType


@runtime_checkable
class HasNameVariant(Protocol):
    """Protocol for resources that have name and variant attributes."""

    def name_variant(self) -> Tuple[str, str]:
        """Returns the name and variant of the resource"""
        ...


@runtime_checkable
class ResourceProtocol(Protocol):
    """Protocol for all Featureform resources."""

    name: str

    def get_resource_type(self) -> ResourceType:
        """Return the resource type."""
        ...

    def operation_type(self) -> OperationType:
        """Return the operation type (CREATE or GET)."""
        ...


@runtime_checkable
class ResourceVariant(HasNameVariant, Protocol):
    """Protocol for resource variants with name, variant, and status."""

    name: str
    variant: str
    server_status: "ServerStatus"  # Forward reference

    def get_resource_type(self) -> ResourceType:
        """Returns the type of the resource"""
        ...

    def to_key(self) -> Tuple[ResourceType, str, str]:
        """Returns a tuple key of (resource_type, name, variant)"""
        return self.get_resource_type(), self.name, self.variant
