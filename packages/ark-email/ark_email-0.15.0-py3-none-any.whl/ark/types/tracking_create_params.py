# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TrackingCreateParams"]


class TrackingCreateParams(TypedDict, total=False):
    domain_id: Required[Annotated[int, PropertyInfo(alias="domainId")]]
    """ID of the sending domain to attach this track domain to"""

    name: Required[str]
    """Subdomain name (e.g., 'track' for track.yourdomain.com)"""

    ssl_enabled: Annotated[Optional[bool], PropertyInfo(alias="sslEnabled")]
    """Enable SSL for tracking URLs (accepts null, defaults to true)"""

    track_clicks: Annotated[Optional[bool], PropertyInfo(alias="trackClicks")]
    """Enable click tracking (accepts null, defaults to true)"""

    track_opens: Annotated[Optional[bool], PropertyInfo(alias="trackOpens")]
    """Enable open tracking (tracking pixel, accepts null, defaults to true)"""
