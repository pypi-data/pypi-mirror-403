# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["WebhookUpdateResponse", "Data"]


class Data(BaseModel):
    id: str
    """Webhook ID"""

    all_events: bool = FieldInfo(alias="allEvents")
    """Whether subscribed to all events"""

    created_at: datetime = FieldInfo(alias="createdAt")

    enabled: bool
    """Whether the webhook is active"""

    events: List[
        Literal[
            "MessageSent",
            "MessageDelayed",
            "MessageDeliveryFailed",
            "MessageHeld",
            "MessageBounced",
            "MessageLinkClicked",
            "MessageLoaded",
            "DomainDNSError",
        ]
    ]
    """Subscribed events"""

    name: str
    """Webhook name for identification"""

    url: str
    """Webhook endpoint URL"""

    uuid: str


class WebhookUpdateResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
