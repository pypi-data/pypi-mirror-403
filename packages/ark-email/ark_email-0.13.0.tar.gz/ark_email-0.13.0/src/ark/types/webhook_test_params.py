# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["WebhookTestParams"]


class WebhookTestParams(TypedDict, total=False):
    event: Required[
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
    """Event type to simulate"""
