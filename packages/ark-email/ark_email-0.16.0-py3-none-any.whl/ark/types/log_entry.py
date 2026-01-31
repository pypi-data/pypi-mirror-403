# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["LogEntry", "Context", "Credential", "RateLimit", "Email", "Error", "SDK"]


class Context(BaseModel):
    """Request context information"""

    idempotency_key: Optional[str] = FieldInfo(alias="idempotencyKey", default=None)
    """Idempotency key if provided"""

    ip_address: Optional[str] = FieldInfo(alias="ipAddress", default=None)
    """Client IP address"""

    query_params: Optional[Dict[str, object]] = FieldInfo(alias="queryParams", default=None)
    """Query parameters"""

    user_agent: Optional[str] = FieldInfo(alias="userAgent", default=None)
    """User-Agent header"""


class Credential(BaseModel):
    """API credential information"""

    id: str
    """Credential ID"""

    key_prefix: Optional[str] = FieldInfo(alias="keyPrefix", default=None)
    """API key prefix (first 8 characters)"""


class RateLimit(BaseModel):
    """Rate limit state at time of request"""

    limit: Optional[int] = None
    """Rate limit ceiling"""

    limited: Optional[bool] = None
    """Whether the request was rate limited"""

    remaining: Optional[int] = None
    """Remaining requests in window"""

    reset: Optional[int] = None
    """Unix timestamp when limit resets"""


class Email(BaseModel):
    """Email-specific data (for email endpoints)"""

    id: Optional[str] = None
    """Email message identifier (token)"""

    recipient_count: Optional[int] = FieldInfo(alias="recipientCount", default=None)
    """Number of recipients"""


class Error(BaseModel):
    """Error details (null if request succeeded)"""

    code: Optional[str] = None
    """Error code"""

    message: Optional[str] = None
    """Error message"""


class SDK(BaseModel):
    """SDK information (null if not using an SDK)"""

    name: Optional[str] = None
    """SDK name"""

    version: Optional[str] = None
    """SDK version"""


class LogEntry(BaseModel):
    """API request log entry (list view)"""

    context: Context
    """Request context information"""

    credential: Credential
    """API credential information"""

    duration_ms: int = FieldInfo(alias="durationMs")
    """Request duration in milliseconds"""

    endpoint: str
    """Semantic endpoint name"""

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    """HTTP method"""

    path: str
    """Request path"""

    rate_limit: RateLimit = FieldInfo(alias="rateLimit")
    """Rate limit state at time of request"""

    request_id: str = FieldInfo(alias="requestId")
    """Unique request identifier"""

    status_code: int = FieldInfo(alias="statusCode")
    """HTTP response status code"""

    timestamp: datetime
    """When the request was made (ISO 8601)"""

    email: Optional[Email] = None
    """Email-specific data (for email endpoints)"""

    error: Optional[Error] = None
    """Error details (null if request succeeded)"""

    sdk: Optional[SDK] = None
    """SDK information (null if not using an SDK)"""
