# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .dns_record import DNSRecord
from .shared.api_meta import APIMeta

__all__ = ["DomainCreateResponse", "Data", "DataDNSRecords"]


class DataDNSRecords(BaseModel):
    dkim: DNSRecord

    return_path: DNSRecord = FieldInfo(alias="returnPath")

    spf: DNSRecord


class Data(BaseModel):
    id: str
    """Domain ID"""

    created_at: datetime = FieldInfo(alias="createdAt")

    dns_records: DataDNSRecords = FieldInfo(alias="dnsRecords")

    name: str
    """Domain name"""

    uuid: str

    verified: bool
    """Whether DNS is verified"""

    verified_at: Optional[datetime] = FieldInfo(alias="verifiedAt", default=None)
    """When the domain was verified (null if not verified)"""


class DomainCreateResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
