# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["SuppressionBulkCreateResponse", "Data"]


class Data(BaseModel):
    added: int
    """Newly suppressed addresses"""

    failed: int
    """Invalid addresses skipped"""

    total_requested: int = FieldInfo(alias="totalRequested")
    """Total addresses in request"""

    updated: int
    """Already suppressed addresses (updated reason)"""


class SuppressionBulkCreateResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
