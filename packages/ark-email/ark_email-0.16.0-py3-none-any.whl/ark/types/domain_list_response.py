# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["DomainListResponse", "Data", "DataDomain"]


class DataDomain(BaseModel):
    id: int
    """Unique domain identifier"""

    name: str
    """The domain name used for sending emails"""

    verified: bool
    """Whether all DNS records (SPF, DKIM, Return Path) are correctly configured.

    Domain must be verified before sending emails.
    """


class Data(BaseModel):
    domains: List[DataDomain]


class DomainListResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
