"""Billing data models for Stripe integration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class PaymentStatus(str, Enum):
    """Payment/Invoice statuses."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


@dataclass
class Customer:
    """Stripe customer representation."""
    id: str
    email: str
    name: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    default_payment_method: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    @property
    def has_payment_method(self) -> bool:
        return self.default_payment_method is not None


@dataclass
class Subscription:
    """Stripe subscription representation."""
    id: str
    customer_id: str
    stripe_subscription_id: str
    tier: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}

    @property
    def days_remaining(self) -> int:
        if self.current_period_end:
            delta = self.current_period_end - datetime.utcnow()
            return max(0, delta.days)
        return 0


@dataclass
class Invoice:
    """Stripe invoice representation."""
    id: str
    customer_id: str
    stripe_invoice_id: str
    subscription_id: Optional[str]
    amount_due: int  # in cents
    amount_paid: int
    currency: str
    status: PaymentStatus
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def amount_due_dollars(self) -> float:
        return self.amount_due / 100

    @property
    def amount_paid_dollars(self) -> float:
        return self.amount_paid / 100


@dataclass
class UsageRecord:
    """Usage record for metered billing."""
    id: str
    subscription_id: str
    quantity: int  # API calls
    timestamp: datetime
    action: str = "increment"  # or "set"
    idempotency_key: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PriceInfo:
    """Pricing information for a tier."""
    tier: str
    stripe_price_id: str
    amount: int  # monthly price in cents
    stripe_product_id: str = ""
    currency: str = "usd"
    interval: str = "month"
    api_calls_included: int = 0
    overage_price_per_call: float = 0.0  # in cents

    @property
    def monthly_price_dollars(self) -> float:
        return self.amount / 100
