# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TrackDomain", "DNSRecord"]


class DNSRecord(BaseModel):
    """Required DNS record configuration"""

    name: Optional[str] = None
    """DNS record name"""

    type: Optional[str] = None
    """DNS record type"""

    value: Optional[str] = None
    """DNS record value (target)"""


class TrackDomain(BaseModel):
    id: str
    """Track domain ID"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the track domain was created"""

    dns_ok: bool = FieldInfo(alias="dnsOk")
    """Whether DNS is correctly configured"""

    domain_id: str = FieldInfo(alias="domainId")
    """ID of the parent sending domain"""

    full_name: str = FieldInfo(alias="fullName")
    """Full domain name"""

    name: str
    """Subdomain name"""

    ssl_enabled: bool = FieldInfo(alias="sslEnabled")
    """Whether SSL is enabled for tracking URLs"""

    track_clicks: bool = FieldInfo(alias="trackClicks")
    """Whether click tracking is enabled"""

    track_opens: bool = FieldInfo(alias="trackOpens")
    """Whether open tracking is enabled"""

    dns_checked_at: Optional[datetime] = FieldInfo(alias="dnsCheckedAt", default=None)
    """When DNS was last checked"""

    dns_error: Optional[str] = FieldInfo(alias="dnsError", default=None)
    """DNS error message if verification failed"""

    dns_record: Optional[DNSRecord] = FieldInfo(alias="dnsRecord", default=None)
    """Required DNS record configuration"""

    dns_status: Optional[Literal["ok", "missing", "invalid"]] = FieldInfo(alias="dnsStatus", default=None)
    """Current DNS verification status"""

    excluded_click_domains: Optional[str] = FieldInfo(alias="excludedClickDomains", default=None)
    """Domains excluded from click tracking"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """When the track domain was last updated"""
