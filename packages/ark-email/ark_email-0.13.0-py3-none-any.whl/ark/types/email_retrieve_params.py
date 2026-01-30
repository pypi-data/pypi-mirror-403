# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["EmailRetrieveParams"]


class EmailRetrieveParams(TypedDict, total=False):
    expand: str
    """Comma-separated list of fields to include:

    - `full` - Include all expanded fields in a single request
    - `content` - HTML and plain text body
    - `headers` - Email headers
    - `deliveries` - Delivery attempt history
    - `activity` - Opens and clicks tracking data
    - `attachments` - File attachments with content (base64 encoded)
    - `raw` - Complete raw MIME message (base64 encoded)
    """
