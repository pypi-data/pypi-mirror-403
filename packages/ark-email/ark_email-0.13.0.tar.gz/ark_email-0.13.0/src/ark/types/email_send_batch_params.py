# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["EmailSendBatchParams", "Email"]


class EmailSendBatchParams(TypedDict, total=False):
    emails: Required[Iterable[Email]]

    from_: Required[Annotated[str, PropertyInfo(alias="from")]]
    """Sender email for all messages"""

    idempotency_key: Annotated[str, PropertyInfo(alias="Idempotency-Key")]


class Email(TypedDict, total=False):
    subject: Required[str]

    to: Required[SequenceNotStr[str]]

    html: Optional[str]

    metadata: Optional[Dict[str, str]]
    """Custom key-value pairs attached to an email for webhook correlation.

    When you send an email with metadata, these key-value pairs are:

    - **Stored** with the message
    - **Returned** in all webhook event payloads (MessageSent, MessageBounced, etc.)
    - **Never visible** to email recipients

    This is useful for correlating webhook events with your internal systems (e.g.,
    user IDs, order IDs, campaign identifiers).

    **Validation Rules:**

    - Maximum 10 keys per email
    - Keys: 1-40 characters, must start with a letter, only alphanumeric and
      underscores (`^[a-zA-Z][a-zA-Z0-9_]*$`)
    - Values: 1-500 characters, no control characters (newlines, tabs, etc.)
    - Total size: 4KB maximum (JSON-encoded)
    """

    tag: Optional[str]
    """Tag for categorization and filtering"""

    text: Optional[str]
