# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["EmailRetrieveDeliveriesResponse", "Data", "DataDelivery", "DataRetryState"]


class DataDelivery(BaseModel):
    id: str
    """Delivery attempt ID"""

    status: str
    """Delivery status (lowercase)"""

    timestamp: float
    """Unix timestamp"""

    timestamp_iso: datetime = FieldInfo(alias="timestampIso")
    """ISO 8601 timestamp"""

    code: Optional[int] = None
    """SMTP response code"""

    details: Optional[str] = None
    """Status details"""

    output: Optional[str] = None
    """SMTP server response from the receiving mail server"""

    sent_with_ssl: Optional[bool] = FieldInfo(alias="sentWithSsl", default=None)
    """Whether TLS was used"""


class DataRetryState(BaseModel):
    """
    Information about the current retry state of a message that is queued for delivery.
    Only present when the message is in the delivery queue.
    """

    attempt: int
    """Current attempt number (0-indexed).

    The first delivery attempt is 0, the first retry is 1, and so on.
    """

    attempts_remaining: int = FieldInfo(alias="attemptsRemaining")
    """
    Number of attempts remaining before the message is hard-failed. Calculated as
    `maxAttempts - attempt`.
    """

    manual: bool
    """
    Whether this queue entry was created by a manual retry request. Manual retries
    bypass certain hold conditions like suppression lists.
    """

    max_attempts: int = FieldInfo(alias="maxAttempts")
    """
    Maximum number of delivery attempts before the message is hard-failed.
    Configured at the server level.
    """

    processing: bool
    """
    Whether the message is currently being processed by a delivery worker. When
    `true`, the message is actively being sent.
    """

    next_retry_at: Optional[float] = FieldInfo(alias="nextRetryAt", default=None)
    """
    Unix timestamp of when the next retry attempt is scheduled. `null` if the
    message is ready for immediate processing or currently being processed.
    """

    next_retry_at_iso: Optional[datetime] = FieldInfo(alias="nextRetryAtIso", default=None)
    """
    ISO 8601 formatted timestamp of the next retry attempt. `null` if the message is
    ready for immediate processing.
    """


class Data(BaseModel):
    can_retry_manually: bool = FieldInfo(alias="canRetryManually")
    """
    Whether the message can be manually retried via `POST /emails/{emailId}/retry`.
    `true` when the raw message content is still available (not expired). Messages
    older than the retention period cannot be retried.
    """

    deliveries: List[DataDelivery]
    """
    Chronological list of delivery attempts for this message. Each attempt includes
    SMTP response codes and timestamps.
    """

    message_id: int = FieldInfo(alias="messageId")
    """Internal numeric message ID"""

    message_token: str = FieldInfo(alias="messageToken")
    """Unique message token for API references"""

    retry_state: Optional[DataRetryState] = FieldInfo(alias="retryState", default=None)
    """
    Information about the current retry state of a message that is queued for
    delivery. Only present when the message is in the delivery queue.
    """

    status: Literal["pending", "sent", "softfail", "hardfail", "held", "bounced"]
    """Current message status (lowercase). Possible values:

    - `pending` - Initial state, awaiting first delivery attempt
    - `sent` - Successfully delivered
    - `softfail` - Temporary failure, will retry automatically
    - `hardfail` - Permanent failure, will not retry
    - `held` - Held for manual review (suppression list, etc.)
    - `bounced` - Bounced by recipient server
    """


class EmailRetrieveDeliveriesResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
