# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.api_meta import APIMeta

__all__ = ["UsageRetrieveResponse", "Data", "DataBilling", "DataBillingAutoRecharge", "DataRateLimit", "DataSendLimit"]


class DataBillingAutoRecharge(BaseModel):
    """Auto-recharge configuration"""

    amount: str
    """Amount to recharge when triggered"""

    enabled: bool
    """Whether auto-recharge is enabled"""

    threshold: str
    """Balance threshold that triggers recharge"""


class DataBilling(BaseModel):
    """Billing and credit information"""

    auto_recharge: DataBillingAutoRecharge = FieldInfo(alias="autoRecharge")
    """Auto-recharge configuration"""

    credit_balance: str = FieldInfo(alias="creditBalance")
    """Current credit balance as formatted string (e.g., "25.50")"""

    credit_balance_cents: int = FieldInfo(alias="creditBalanceCents")
    """Current credit balance in cents for precise calculations"""

    has_payment_method: bool = FieldInfo(alias="hasPaymentMethod")
    """Whether a payment method is configured"""


class DataRateLimit(BaseModel):
    """API rate limit status"""

    limit: int
    """Maximum requests allowed per period"""

    period: Literal["second"]
    """Time period for the limit"""

    remaining: int
    """Requests remaining in current window"""

    reset: int
    """Unix timestamp when the limit resets"""


class DataSendLimit(BaseModel):
    """Email send limit status (hourly cap)"""

    approaching: bool
    """Whether approaching the limit (>90%)"""

    exceeded: bool
    """Whether the limit has been exceeded"""

    limit: Optional[int] = None
    """Maximum emails allowed per hour (null = unlimited)"""

    period: Literal["hour"]
    """Time period for the limit"""

    remaining: Optional[int] = None
    """Emails remaining in current period (null if unlimited)"""

    resets_at: datetime = FieldInfo(alias="resetsAt")
    """ISO timestamp when the limit window resets (top of next hour)"""

    usage_percent: Optional[float] = FieldInfo(alias="usagePercent", default=None)
    """Usage as a percentage (null if unlimited)"""

    used: int
    """Emails sent in current period"""


class Data(BaseModel):
    """Current usage and limit information"""

    billing: Optional[DataBilling] = None
    """Billing and credit information"""

    rate_limit: DataRateLimit = FieldInfo(alias="rateLimit")
    """API rate limit status"""

    send_limit: Optional[DataSendLimit] = FieldInfo(alias="sendLimit", default=None)
    """Email send limit status (hourly cap)"""


class UsageRetrieveResponse(BaseModel):
    """Account usage and limits response"""

    data: Data
    """Current usage and limit information"""

    meta: APIMeta

    success: Literal[True]
