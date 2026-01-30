# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["LogListParams"]


class LogListParams(TypedDict, total=False):
    credential_id: Annotated[str, PropertyInfo(alias="credentialId")]
    """Filter by API credential ID"""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """Filter logs before this date (ISO 8601 format)"""

    endpoint: str
    """Filter by endpoint name"""

    page: int
    """Page number"""

    per_page: Annotated[int, PropertyInfo(alias="perPage")]
    """Results per page (max 100)"""

    request_id: Annotated[str, PropertyInfo(alias="requestId")]
    """Filter by request ID (partial match)"""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """Filter logs after this date (ISO 8601 format)"""

    status: Literal["success", "error"]
    """Filter by status category:

    - `success` - Status codes < 400
    - `error` - Status codes >= 400
    """

    status_code: Annotated[int, PropertyInfo(alias="statusCode")]
    """Filter by exact HTTP status code (100-599)"""
