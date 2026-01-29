# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["EmailRetrieveParams"]


class EmailRetrieveParams(TypedDict, total=False):
    expand: str
    """Comma-separated list of fields to include:

    - `content` - HTML and plain text body
    - `headers` - Email headers
    - `deliveries` - Delivery attempt history
    - `activity` - Opens and clicks
    """
