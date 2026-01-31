# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["EmailSendRawParams"]


class EmailSendRawParams(TypedDict, total=False):
    from_: Required[Annotated[str, PropertyInfo(alias="from")]]
    """Sender email address. Must be from a verified domain.

    **Supported formats:**

    - Email only: `hello@yourdomain.com`
    - With display name: `Acme <hello@yourdomain.com>`
    - With quoted name: `"Acme Support" <support@yourdomain.com>`

    The domain portion must match a verified sending domain in your account.
    """

    raw_message: Required[Annotated[str, PropertyInfo(alias="rawMessage")]]
    """Base64-encoded RFC 2822 MIME message.

    **You must base64-encode your raw email before sending.** The raw email should
    include headers (From, To, Subject, Content-Type, etc.) followed by a blank line
    and the message body.
    """

    to: Required[SequenceNotStr[str]]
    """Recipient email addresses"""

    bounce: Optional[bool]
    """Whether this is a bounce message (accepts null)"""
