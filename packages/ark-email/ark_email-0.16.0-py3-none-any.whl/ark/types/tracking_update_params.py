# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TrackingUpdateParams"]


class TrackingUpdateParams(TypedDict, total=False):
    excluded_click_domains: Annotated[Optional[str], PropertyInfo(alias="excludedClickDomains")]
    """Comma-separated list of domains to exclude from click tracking (accepts null)"""

    ssl_enabled: Annotated[Optional[bool], PropertyInfo(alias="sslEnabled")]
    """Enable or disable SSL for tracking URLs (accepts null)"""

    track_clicks: Annotated[Optional[bool], PropertyInfo(alias="trackClicks")]
    """Enable or disable click tracking (accepts null)"""

    track_opens: Annotated[Optional[bool], PropertyInfo(alias="trackOpens")]
    """Enable or disable open tracking (accepts null)"""
