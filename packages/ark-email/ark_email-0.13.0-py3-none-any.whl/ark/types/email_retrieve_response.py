# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = [
    "EmailRetrieveResponse",
    "Data",
    "DataActivity",
    "DataActivityClick",
    "DataActivityOpen",
    "DataAttachment",
    "DataDelivery",
]


class DataActivityClick(BaseModel):
    ip_address: Optional[str] = FieldInfo(alias="ipAddress", default=None)
    """IP address of the clicker"""

    timestamp: Optional[float] = None
    """Unix timestamp of the click event"""

    timestamp_iso: Optional[datetime] = FieldInfo(alias="timestampIso", default=None)
    """ISO 8601 timestamp of the click event"""

    url: Optional[str] = None
    """URL that was clicked"""

    user_agent: Optional[str] = FieldInfo(alias="userAgent", default=None)
    """User agent of the email client"""


class DataActivityOpen(BaseModel):
    ip_address: Optional[str] = FieldInfo(alias="ipAddress", default=None)
    """IP address of the opener"""

    timestamp: Optional[float] = None
    """Unix timestamp of the open event"""

    timestamp_iso: Optional[datetime] = FieldInfo(alias="timestampIso", default=None)
    """ISO 8601 timestamp of the open event"""

    user_agent: Optional[str] = FieldInfo(alias="userAgent", default=None)
    """User agent of the email client"""


class DataActivity(BaseModel):
    """Opens and clicks tracking data (included if expand=activity)"""

    clicks: Optional[List[DataActivityClick]] = None
    """List of link click events"""

    opens: Optional[List[DataActivityOpen]] = None
    """List of email open events"""


class DataAttachment(BaseModel):
    """An email attachment retrieved from a sent message"""

    content_type: str = FieldInfo(alias="contentType")
    """MIME type of the attachment"""

    data: str
    """Base64 encoded attachment content. Decode this to get the raw file bytes."""

    filename: str
    """Original filename of the attachment"""

    hash: str
    """SHA256 hash of the attachment content for verification"""

    size: int
    """Size of the attachment in bytes"""


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


class Data(BaseModel):
    id: str
    """Internal message ID"""

    token: str
    """
    Unique message token used to retrieve this email via API. Combined with id to
    form the full message identifier: msg*{id}*{token} Use this token with GET
    /emails/{emailId} where emailId = "msg*{id}*{token}"
    """

    from_: str = FieldInfo(alias="from")
    """Sender address"""

    scope: Literal["outgoing", "incoming"]
    """Message direction"""

    status: Literal["pending", "sent", "softfail", "hardfail", "bounced", "held"]
    """Current delivery status:

    - `pending` - Email accepted, waiting to be processed
    - `sent` - Email transmitted to recipient's mail server
    - `softfail` - Temporary delivery failure, will retry
    - `hardfail` - Permanent delivery failure
    - `bounced` - Email bounced back
    - `held` - Held for manual review
    """

    subject: str
    """Email subject line"""

    timestamp: float
    """Unix timestamp when the email was sent"""

    timestamp_iso: datetime = FieldInfo(alias="timestampIso")
    """ISO 8601 formatted timestamp"""

    to: str
    """Recipient address"""

    activity: Optional[DataActivity] = None
    """Opens and clicks tracking data (included if expand=activity)"""

    attachments: Optional[List[DataAttachment]] = None
    """File attachments (included if expand=attachments)"""

    deliveries: Optional[List[DataDelivery]] = None
    """Delivery attempt history (included if expand=deliveries)"""

    headers: Optional[Dict[str, str]] = None
    """Email headers (included if expand=headers)"""

    html_body: Optional[str] = FieldInfo(alias="htmlBody", default=None)
    """HTML body content (included if expand=content)"""

    message_id: Optional[str] = FieldInfo(alias="messageId", default=None)
    """SMTP Message-ID header"""

    plain_body: Optional[str] = FieldInfo(alias="plainBody", default=None)
    """Plain text body (included if expand=content)"""

    raw_message: Optional[str] = FieldInfo(alias="rawMessage", default=None)
    """
    Complete raw MIME message, base64 encoded (included if expand=raw). Decode this
    to get the original RFC 2822 formatted email.
    """

    spam: Optional[bool] = None
    """Whether the message was flagged as spam"""

    spam_score: Optional[float] = FieldInfo(alias="spamScore", default=None)
    """Spam score (if applicable)"""

    tag: Optional[str] = None
    """Optional categorization tag"""


class EmailRetrieveResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
