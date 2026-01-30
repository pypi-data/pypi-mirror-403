# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, TypedDict

__all__ = ["SuppressionBulkCreateParams", "Suppression"]


class SuppressionBulkCreateParams(TypedDict, total=False):
    suppressions: Required[Iterable[Suppression]]


class Suppression(TypedDict, total=False):
    address: Required[str]

    reason: Optional[str]
    """Reason for suppression (accepts null)"""
