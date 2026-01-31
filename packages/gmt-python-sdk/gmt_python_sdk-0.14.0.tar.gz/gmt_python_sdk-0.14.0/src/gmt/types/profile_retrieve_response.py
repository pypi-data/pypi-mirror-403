# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = [
    "ProfileRetrieveResponse",
    "Balance",
    "Discount",
    "Referral",
    "ReferralBalance",
    "ReferralProfit",
    "Statistics",
]


class Balance(BaseModel):
    amount: str
    """Monetary amount as a string with up to 2 decimal places."""

    currency_code: str
    """ISO 4217 currency code."""


class Discount(BaseModel):
    level: Literal["none", "bronze", "silver", "gold", "platinum", "premium"]
    """Current discount level: none, bronze, silver, gold, platinum, premium."""

    percent: float
    """Discount percentage."""


class ReferralBalance(BaseModel):
    """Current referral balance available for withdrawal."""

    amount: str
    """Monetary amount as a string with up to 2 decimal places."""

    currency_code: str
    """ISO 4217 currency code."""


class ReferralProfit(BaseModel):
    """Total lifetime earnings from referral commissions."""

    amount: str
    """Monetary amount as a string with up to 2 decimal places."""

    currency_code: str
    """ISO 4217 currency code."""


class Referral(BaseModel):
    balance: ReferralBalance
    """Current referral balance available for withdrawal."""

    level: Literal["bronze", "silver", "gold", "platinum"]
    """Current referral program level: bronze, silver, gold, platinum."""

    percent: float
    """Referral commission percentage."""

    profit: ReferralProfit
    """Total lifetime earnings from referral commissions."""

    referrals_count: int
    """Total number of users invited through referral link."""


class Statistics(BaseModel):
    total_purchases: int
    """Total number of successful purchases."""


class ProfileRetrieveResponse(BaseModel):
    """Successful response."""

    id: str
    """User Database ID"""

    balance: Balance

    created_at: str
    """Account creation time in ISO 8601 format (UTC)"""

    discount: Discount

    login: Optional[str] = None
    """Web username"""

    referral: Referral

    statistics: Statistics

    telegram_id: Optional[str] = None
    """User's Telegram ID (null for web-only users)"""

    telegram_username: Optional[str] = None
    """User's Telegram username"""
