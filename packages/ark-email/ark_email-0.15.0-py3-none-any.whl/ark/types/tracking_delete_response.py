# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["TrackingDeleteResponse", "Data"]


class Data(BaseModel):
    message: str


class TrackingDeleteResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
