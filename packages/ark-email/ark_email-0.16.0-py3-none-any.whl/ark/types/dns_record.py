# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["DNSRecord"]


class DNSRecord(BaseModel):
    """A DNS record that needs to be configured in your domain's DNS settings.

    The `name` field contains the relative hostname to enter in your DNS provider (which auto-appends the zone).
    The `fullName` field contains the complete fully-qualified domain name (FQDN) for reference.

    **Example for subdomain `mail.example.com`:**
    - `name`: `"mail"` (what you enter in DNS provider)
    - `fullName`: `"mail.example.com"` (the complete hostname)

    **Example for root domain `example.com`:**
    - `name`: `"@"` (DNS shorthand for apex/root)
    - `fullName`: `"example.com"`
    """

    full_name: str = FieldInfo(alias="fullName")
    """
    The complete fully-qualified domain name (FQDN). Use this as a reference to
    verify the record is configured correctly.
    """

    name: str
    """
    The relative hostname to enter in your DNS provider. Most DNS providers
    auto-append the zone name, so you only need to enter this relative part.

    - `"@"` means the apex/root of the zone (for root domains)
    - `"mail"` for a subdomain like `mail.example.com`
    - `"ark-xyz._domainkey.mail"` for DKIM on a subdomain
    """

    type: Literal["TXT", "CNAME", "MX"]
    """The DNS record type to create"""

    value: str
    """The value to set for the DNS record"""

    status: Optional[Literal["OK", "Missing", "Invalid"]] = None
    """Current verification status of this DNS record:

    - `OK` - Record is correctly configured and verified
    - `Missing` - Record was not found in your DNS
    - `Invalid` - Record exists but has an incorrect value
    - `null` - Record has not been checked yet
    """
