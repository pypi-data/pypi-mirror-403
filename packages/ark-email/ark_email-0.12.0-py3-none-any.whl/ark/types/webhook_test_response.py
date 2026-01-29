# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["WebhookTestResponse", "Data"]


class Data(BaseModel):
    duration: int
    """Request duration in milliseconds"""

    event: str
    """Event type that was tested"""

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)
    """HTTP status code from the webhook endpoint"""

    success: bool
    """Whether the webhook endpoint responded with a 2xx status"""

    body: Optional[str] = None
    """Response body from the webhook endpoint (truncated if too long)"""

    error: Optional[str] = None
    """Error message if the request failed"""


class WebhookTestResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
