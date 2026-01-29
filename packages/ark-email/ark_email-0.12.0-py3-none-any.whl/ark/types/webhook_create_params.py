# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["WebhookCreateParams"]


class WebhookCreateParams(TypedDict, total=False):
    name: Required[str]
    """Webhook name for identification"""

    url: Required[str]
    """HTTPS endpoint URL"""

    all_events: Annotated[Optional[bool], PropertyInfo(alias="allEvents")]
    """Subscribe to all events (ignores events array, accepts null)"""

    enabled: Optional[bool]
    """Whether the webhook is enabled (accepts null)"""

    events: Optional[
        List[
            Literal[
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
        ]
    ]
    """Events to subscribe to (accepts null):

    - `MessageSent` - Email successfully delivered to recipient's server
    - `MessageDelayed` - Temporary delivery failure, will retry
    - `MessageDeliveryFailed` - Permanent delivery failure
    - `MessageHeld` - Email held for manual review
    - `MessageBounced` - Email bounced back
    - `MessageLinkClicked` - Recipient clicked a tracked link
    - `MessageLoaded` - Recipient opened the email (tracking pixel loaded)
    - `DomainDNSError` - DNS configuration issue detected
    """
