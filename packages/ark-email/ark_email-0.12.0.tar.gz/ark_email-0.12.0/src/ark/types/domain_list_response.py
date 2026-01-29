# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["DomainListResponse", "Data", "DataDomain"]


class DataDomain(BaseModel):
    id: str
    """Domain ID"""

    dns_ok: bool = FieldInfo(alias="dnsOk")

    name: str

    verified: bool


class Data(BaseModel):
    domains: List[DataDomain]


class DomainListResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
