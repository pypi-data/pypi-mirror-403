# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["TrackingVerifyResponse", "Data", "DataDNSRecord"]


class DataDNSRecord(BaseModel):
    """Required DNS record configuration"""

    name: Optional[str] = None

    type: Optional[str] = None

    value: Optional[str] = None


class Data(BaseModel):
    id: str
    """Track domain ID"""

    dns_ok: bool = FieldInfo(alias="dnsOk")
    """Whether DNS is correctly configured"""

    dns_status: Optional[Literal["ok", "missing", "invalid"]] = FieldInfo(alias="dnsStatus", default=None)
    """Current DNS verification status"""

    full_name: str = FieldInfo(alias="fullName")
    """Full domain name"""

    dns_checked_at: Optional[datetime] = FieldInfo(alias="dnsCheckedAt", default=None)
    """When DNS was last checked"""

    dns_error: Optional[str] = FieldInfo(alias="dnsError", default=None)
    """DNS error message if verification failed"""

    dns_record: Optional[DataDNSRecord] = FieldInfo(alias="dnsRecord", default=None)
    """Required DNS record configuration"""


class TrackingVerifyResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
