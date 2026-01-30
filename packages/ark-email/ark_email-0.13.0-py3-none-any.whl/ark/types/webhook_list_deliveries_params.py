# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["WebhookListDeliveriesParams"]


class WebhookListDeliveriesParams(TypedDict, total=False):
    after: int
    """Only deliveries after this Unix timestamp"""

    before: int
    """Only deliveries before this Unix timestamp"""

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
    """Filter by event type"""

    page: int
    """Page number (default 1)"""

    per_page: Annotated[int, PropertyInfo(alias="perPage")]
    """Items per page (default 30, max 100)"""

    success: bool
    """Filter by delivery success (true = 2xx response, false = non-2xx or error)"""
