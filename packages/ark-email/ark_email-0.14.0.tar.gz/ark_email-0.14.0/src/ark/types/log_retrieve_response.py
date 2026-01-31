# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .shared.api_meta import APIMeta
from .log_entry_detail import LogEntryDetail

__all__ = ["LogRetrieveResponse"]


class LogRetrieveResponse(BaseModel):
    """Detailed API request log with request/response bodies"""

    data: LogEntryDetail
    """Full API request log entry with bodies"""

    meta: APIMeta

    success: Literal[True]
