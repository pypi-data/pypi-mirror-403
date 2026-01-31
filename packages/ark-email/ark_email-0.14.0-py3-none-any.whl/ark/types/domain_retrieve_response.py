# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .dns_record import DNSRecord
from .shared.api_meta import APIMeta

__all__ = ["DomainRetrieveResponse", "Data", "DataDNSRecords"]


class DataDNSRecords(BaseModel):
    """DNS records that must be added to your domain's DNS settings.

    Null if records are not yet generated.

    **Important:** The `name` field contains the relative hostname that you should enter in your DNS provider.
    Most DNS providers auto-append the zone name, so you only need to enter the relative part.

    For subdomains like `mail.example.com`, the zone is `example.com`, so:
    - SPF `name` would be `mail` (not `@`)
    - DKIM `name` would be `ark-xyz._domainkey.mail`
    - Return Path `name` would be `psrp.mail`
    """

    dkim: Optional[DNSRecord] = None
    """A DNS record that needs to be configured in your domain's DNS settings.

    The `name` field contains the relative hostname to enter in your DNS provider
    (which auto-appends the zone). The `fullName` field contains the complete
    fully-qualified domain name (FQDN) for reference.

    **Example for subdomain `mail.example.com`:**

    - `name`: `"mail"` (what you enter in DNS provider)
    - `fullName`: `"mail.example.com"` (the complete hostname)

    **Example for root domain `example.com`:**

    - `name`: `"@"` (DNS shorthand for apex/root)
    - `fullName`: `"example.com"`
    """

    return_path: Optional[DNSRecord] = FieldInfo(alias="returnPath", default=None)
    """A DNS record that needs to be configured in your domain's DNS settings.

    The `name` field contains the relative hostname to enter in your DNS provider
    (which auto-appends the zone). The `fullName` field contains the complete
    fully-qualified domain name (FQDN) for reference.

    **Example for subdomain `mail.example.com`:**

    - `name`: `"mail"` (what you enter in DNS provider)
    - `fullName`: `"mail.example.com"` (the complete hostname)

    **Example for root domain `example.com`:**

    - `name`: `"@"` (DNS shorthand for apex/root)
    - `fullName`: `"example.com"`
    """

    spf: Optional[DNSRecord] = None
    """A DNS record that needs to be configured in your domain's DNS settings.

    The `name` field contains the relative hostname to enter in your DNS provider
    (which auto-appends the zone). The `fullName` field contains the complete
    fully-qualified domain name (FQDN) for reference.

    **Example for subdomain `mail.example.com`:**

    - `name`: `"mail"` (what you enter in DNS provider)
    - `fullName`: `"mail.example.com"` (the complete hostname)

    **Example for root domain `example.com`:**

    - `name`: `"@"` (DNS shorthand for apex/root)
    - `fullName`: `"example.com"`
    """

    zone: Optional[str] = None
    """
    The DNS zone (registrable domain) where records should be added. This is the
    root domain that your DNS provider manages. For `mail.example.com`, the zone is
    `example.com`. For `example.co.uk`, the zone is `example.co.uk`.
    """


class Data(BaseModel):
    id: int
    """Unique domain identifier"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """Timestamp when the domain was added"""

    dns_records: Optional[DataDNSRecords] = FieldInfo(alias="dnsRecords", default=None)
    """DNS records that must be added to your domain's DNS settings.

    Null if records are not yet generated.

    **Important:** The `name` field contains the relative hostname that you should
    enter in your DNS provider. Most DNS providers auto-append the zone name, so you
    only need to enter the relative part.

    For subdomains like `mail.example.com`, the zone is `example.com`, so:

    - SPF `name` would be `mail` (not `@`)
    - DKIM `name` would be `ark-xyz._domainkey.mail`
    - Return Path `name` would be `psrp.mail`
    """

    name: str
    """The domain name used for sending emails"""

    uuid: str
    """UUID of the domain"""

    verified: bool
    """Whether all DNS records (SPF, DKIM, Return Path) are correctly configured.

    Domain must be verified before sending emails.
    """

    verified_at: Optional[datetime] = FieldInfo(alias="verifiedAt", default=None)
    """Timestamp when the domain ownership was verified, or null if not yet verified"""


class DomainRetrieveResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
