"""Shared DataMaker types used across v1 and v2 schemas.

This module contains types and utilities common to both DataMaker schema versions.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class DMVersion(StrEnum):
    """DataMaker schema version."""

    V1 = 'v1'
    V2 = 'v2'


class DMAttribute(BaseModel):
    """Attribute on an annotation (shared between v1/v2).

    Attributes:
        name: Attribute name.
        value: Attribute value (string, number, boolean, or list).
    """

    name: str
    value: str | int | float | bool | list[str]


__all__ = [
    'DMAttribute',
    'DMVersion',
]
