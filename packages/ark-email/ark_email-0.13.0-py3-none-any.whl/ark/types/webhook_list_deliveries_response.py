# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["WebhookListDeliveriesResponse", "Data"]


class Data(BaseModel):
    """Summary of a webhook delivery attempt"""

    id: str
    """Unique delivery ID (UUID)"""

    attempt: int
    """Attempt number (1 for first attempt, increments with retries)"""

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

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)
    """HTTP status code returned by the endpoint (null if connection failed)"""

    success: bool
    """Whether the delivery was successful (2xx response)"""

    timestamp: datetime
    """When this delivery attempt occurred"""

    url: str
    """URL the webhook was delivered to"""

    webhook_id: str = FieldInfo(alias="webhookId")
    """ID of the webhook this delivery belongs to"""

    will_retry: bool = FieldInfo(alias="willRetry")
    """Whether this delivery will be retried (true if failed and retries remaining)"""


class WebhookListDeliveriesResponse(BaseModel):
    """Paginated list of webhook delivery attempts"""

    data: List[Data]

    meta: APIMeta

    page: int
    """Current page number"""

    per_page: int = FieldInfo(alias="perPage")
    """Items per page"""

    total: int
    """Total number of deliveries matching the filter"""

    total_pages: int = FieldInfo(alias="totalPages")
    """Total number of pages"""
