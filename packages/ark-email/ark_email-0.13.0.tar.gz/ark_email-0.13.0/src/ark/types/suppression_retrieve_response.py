# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["SuppressionRetrieveResponse", "Data"]


class Data(BaseModel):
    address: str
    """The email address that was checked"""

    suppressed: bool
    """Whether the address is currently suppressed"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """When the suppression was created (if suppressed)"""

    reason: Optional[str] = None
    """Reason for suppression (if suppressed)"""


class SuppressionRetrieveResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
