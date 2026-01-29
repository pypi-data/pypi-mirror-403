# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["SuppressionCreateResponse", "Data"]


class Data(BaseModel):
    id: str
    """Suppression ID"""

    address: str

    created_at: datetime = FieldInfo(alias="createdAt")

    reason: Optional[str] = None
    """Reason for suppression"""


class SuppressionCreateResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
