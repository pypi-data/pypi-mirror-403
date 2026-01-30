# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["WebhookRetrieveDeliveryResponse", "Data", "DataRequest", "DataResponse"]


class DataRequest(BaseModel):
    """The request that was sent to your endpoint"""

    headers: Dict[str, str]
    """HTTP headers that were sent with the request"""

    payload: Dict[str, object]
    """The complete webhook payload that was sent"""


class DataResponse(BaseModel):
    """The response received from your endpoint"""

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)
    """HTTP status code from your endpoint"""

    body: Optional[str] = None
    """Response body from your endpoint (may be truncated)"""


class Data(BaseModel):
    """Full details of a webhook delivery including request and response"""

    id: str
    """Unique delivery ID (UUID)"""

    attempt: int
    """Attempt number for this delivery"""

    event: Literal[
        "MessageSent",
        "MessageDelayed",
        "MessageDeliveryFailed",
        "MessageHeld",
        "MessageBounced",
        "MessageLinkClicked",
        "MessageLoaded",
        "DomainDNSError",
        "SendLimitApproaching",
        "SendLimitExceeded",
    ]
    """Event type that triggered this delivery"""

    request: DataRequest
    """The request that was sent to your endpoint"""

    response: DataResponse
    """The response received from your endpoint"""

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)
    """HTTP status code returned by the endpoint"""

    success: bool
    """Whether the delivery was successful (2xx response)"""

    timestamp: datetime
    """When this delivery attempt occurred"""

    url: str
    """URL the webhook was delivered to"""

    webhook_id: str = FieldInfo(alias="webhookId")
    """ID of the webhook this delivery belongs to"""

    webhook_name: str = FieldInfo(alias="webhookName")
    """Name of the webhook for easy identification"""

    will_retry: bool = FieldInfo(alias="willRetry")
    """Whether this delivery will be retried"""


class WebhookRetrieveDeliveryResponse(BaseModel):
    """Detailed information about a webhook delivery attempt"""

    data: Data
    """Full details of a webhook delivery including request and response"""

    meta: APIMeta

    success: Literal[True]
