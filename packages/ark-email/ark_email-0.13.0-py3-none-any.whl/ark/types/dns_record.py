# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["DNSRecord"]


class DNSRecord(BaseModel):
    name: str
    """DNS record name (hostname)"""

    type: Literal["TXT", "CNAME", "MX"]
    """DNS record type"""

    value: str
    """DNS record value"""

    status: Optional[Literal["OK", "Missing", "Invalid"]] = None
    """DNS verification status:

    - `OK` - Record is correctly configured
    - `Missing` - Record not found in DNS
    - `Invalid` - Record exists but has wrong value
    - `null` - Not yet checked
    """
