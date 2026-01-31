# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .log_entry import LogEntry

__all__ = ["LogEntryDetail", "LogEntryDetailRequest", "LogEntryDetailResponse"]


class LogEntryDetailRequest(BaseModel):
    """Request body information"""

    body: Union[Dict[str, object], str, None] = None
    """Decrypted request body (JSON or string). Bodies over 25KB are truncated."""

    body_size: Optional[int] = FieldInfo(alias="bodySize", default=None)
    """Original request body size in bytes"""


class LogEntryDetailResponse(BaseModel):
    """Response body information"""

    body: Union[Dict[str, object], str, None] = None
    """Decrypted response body (JSON or string). Bodies over 25KB are truncated."""

    body_size: Optional[int] = FieldInfo(alias="bodySize", default=None)
    """Response body size in bytes"""


class LogEntryDetail(LogEntry):
    """Full API request log entry with bodies"""

    request: Optional[LogEntryDetailRequest] = None
    """Request body information"""

    response: Optional[LogEntryDetailResponse] = None
    """Response body information"""
