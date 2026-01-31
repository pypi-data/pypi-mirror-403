# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .track_domain import TrackDomain
from .shared.api_meta import APIMeta

__all__ = ["TrackingListResponse", "Data"]


class Data(BaseModel):
    track_domains: List[TrackDomain] = FieldInfo(alias="trackDomains")


class TrackingListResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
