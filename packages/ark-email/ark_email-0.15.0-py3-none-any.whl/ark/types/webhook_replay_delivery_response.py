# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["WebhookReplayDeliveryResponse", "Data"]


class Data(BaseModel):
    duration: int
    """Request duration in milliseconds"""

    new_delivery_id: str = FieldInfo(alias="newDeliveryId")
    """ID of the new delivery created by the replay"""

    original_delivery_id: str = FieldInfo(alias="originalDeliveryId")
    """ID of the original delivery that was replayed"""

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)
    """HTTP status code from your endpoint"""

    success: bool
    """Whether the replay was successful (2xx response from endpoint)"""

    timestamp: datetime
    """When the replay was executed"""


class WebhookReplayDeliveryResponse(BaseModel):
    """Result of replaying a webhook delivery"""

    data: Data

    meta: APIMeta

    success: Literal[True]
