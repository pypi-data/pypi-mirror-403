# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["SuppressionListResponse"]


class SuppressionListResponse(BaseModel):
    id: str
    """Suppression ID"""

    address: str

    created_at: datetime = FieldInfo(alias="createdAt")

    reason: Optional[str] = None
