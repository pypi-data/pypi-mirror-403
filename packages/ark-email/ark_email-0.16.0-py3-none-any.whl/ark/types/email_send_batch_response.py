# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from typing_extensions import Literal

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["EmailSendBatchResponse", "Data", "DataMessages"]


class DataMessages(BaseModel):
    id: str
    """Message identifier (token)"""


class Data(BaseModel):
    accepted: int
    """Successfully accepted emails"""

    failed: int
    """Failed emails"""

    messages: Dict[str, DataMessages]
    """Map of recipient email to message info"""

    total: int
    """Total emails in the batch"""

    sandbox: Optional[bool] = None
    """
    Whether this batch was sent in sandbox mode. Only present (and true) for sandbox
    emails sent from @arkhq.io addresses.
    """


class EmailSendBatchResponse(BaseModel):
    data: Data

    meta: APIMeta

    success: Literal[True]
