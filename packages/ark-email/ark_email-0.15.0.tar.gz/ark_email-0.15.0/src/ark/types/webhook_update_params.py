# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["WebhookUpdateParams"]


class WebhookUpdateParams(TypedDict, total=False):
    all_events: Annotated[Optional[bool], PropertyInfo(alias="allEvents")]

    enabled: Optional[bool]

    events: Optional[SequenceNotStr[str]]

    name: Optional[str]

    url: Optional[str]
