# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .track_domain import TrackDomain
from .shared.api_meta import APIMeta

__all__ = ["TrackingRetrieveResponse"]


class TrackingRetrieveResponse(BaseModel):
    data: TrackDomain

    meta: APIMeta

    success: Literal[True]
