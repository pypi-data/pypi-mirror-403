# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["APIMeta"]


class APIMeta(BaseModel):
    request_id: str = FieldInfo(alias="requestId")
    """Unique request identifier for debugging and support"""
