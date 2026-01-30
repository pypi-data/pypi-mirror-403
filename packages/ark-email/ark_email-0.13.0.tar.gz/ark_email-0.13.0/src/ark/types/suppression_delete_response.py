# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["SuppressionDeleteResponse", "Data"]


class Data(BaseModel):
    message: str


class SuppressionDeleteResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
