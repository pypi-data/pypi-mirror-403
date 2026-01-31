"""
Stripe Billing Service for QuantumFlow.

Handles:
- Customer management
- Subscription lifecycle (create, update, cancel)
- Usage-based billing (metered API calls)
- Webhook processing
- Invoice management
"""

import os
from datetime import datetime
from enum import Enum
from typing import Optional
import stripe

from quantumflow.billing.models import (
    Customer,
    Subscription,
    Invoice,
    UsageRecord,
    SubscriptionStatus,
    PaymentStatus,
    PriceInfo,
)


class SubscriptionTier(str, Enum):
    """Available subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Tier configuration
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "api_calls_monthly": 1_000,
        "max_qubits": 20,
        "backends": ["simulator"],
        "support": "community",
        "rate_limit_per_minute": 10,
    },
    SubscriptionTier.PRO: {
        "api_calls_monthly": 50_000,
        "max_qubits": 100,
        "backends": ["simulator", "ibm", "aws"],
        "support": "email",
        "rate_limit_per_minute": 100,
    },
    SubscriptionTier.ENTERPRISE: {
        "api_calls_monthly": 1_000_000,
        "max_qubits": 156,
        "backends": ["simulator", "ibm", "aws", "dedicated"],
        "support": "24/7",
        "rate_limit_per_minute": 1000,
    },
}

# Stripe product IDs (set in environment)
STRIPE_PRODUCTS = {
    SubscriptionTier.FREE: os.getenv("STRIPE_PRODUCT_FREE", "prod_TsZuC9LFEZGZ6v"),
    SubscriptionTier.PRO: os.getenv("STRIPE_PRODUCT_PRO", "prod_TsZujvgfFU5BFj"),
    SubscriptionTier.ENTERPRISE: os.getenv("STRIPE_PRODUCT_ENTERPRISE", "prod_TsZudz3o7YX9t0"),
}

# Stripe price IDs (set these in environment or Stripe dashboard)
TIER_PRICES = {
    SubscriptionTier.FREE: PriceInfo(
        tier="free",
        stripe_price_id=os.getenv("STRIPE_PRICE_FREE", ""),  # Will be fetched from product
        stripe_product_id=STRIPE_PRODUCTS[SubscriptionTier.FREE],
        amount=0,
        api_calls_included=1_000,
        overage_price_per_call=0.01,
    ),
    SubscriptionTier.PRO: PriceInfo(
        tier="pro",
        stripe_price_id=os.getenv("STRIPE_PRICE_PRO", ""),  # Will be fetched from product
        stripe_product_id=STRIPE_PRODUCTS[SubscriptionTier.PRO],
        amount=4900,  # $49/month
        api_calls_included=50_000,
        overage_price_per_call=0.005,
    ),
    SubscriptionTier.ENTERPRISE: PriceInfo(
        tier="enterprise",
        stripe_price_id=os.getenv("STRIPE_PRICE_ENTERPRISE", ""),  # Will be fetched from product
        stripe_product_id=STRIPE_PRODUCTS[SubscriptionTier.ENTERPRISE],
        amount=19900,  # $199/month
        api_calls_included=1_000_000,
        overage_price_per_call=0.001,  # $0.00001 per call
    ),
}


class StripeService:
    """Service for managing Stripe billing operations."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stripe service.

        Args:
            api_key: Stripe secret key. Defaults to STRIPE_SECRET_KEY env var.
        """
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            raise ValueError("Stripe API key not configured. Set STRIPE_SECRET_KEY.")

        stripe.api_key = self.api_key
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self._price_cache = {}  # Cache for price IDs

    def get_price_id_for_tier(self, tier: SubscriptionTier) -> str:
        """Get the Stripe price ID for a tier, fetching from product if needed."""
        price_info = TIER_PRICES[tier]

        # If price ID is set in env, use it
        if price_info.stripe_price_id:
            return price_info.stripe_price_id

        # Check cache
        if tier in self._price_cache:
            return self._price_cache[tier]

        # Fetch from product
        product_id = price_info.stripe_product_id
        if not product_id:
            raise ValueError(f"No product ID configured for tier {tier}")

        # Get the default price for this product
        prices = stripe.Price.list(product=product_id, active=True, limit=1)
        if not prices.data:
            raise ValueError(f"No active price found for product {product_id}")

        price_id = prices.data[0].id
        self._price_cache[tier] = price_id
        return price_id

    # ==================== Customer Management ====================

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Customer:
        """Create a new Stripe customer."""
        customer_data = {
            "email": email,
            "metadata": metadata or {},
        }
        if name:
            customer_data["name"] = name
        if user_id:
            customer_data["metadata"]["user_id"] = user_id

        stripe_customer = stripe.Customer.create(**customer_data)

        return Customer(
            id=user_id or stripe_customer.id,
            email=email,
            name=name,
            stripe_customer_id=stripe_customer.id,
            metadata=stripe_customer.metadata,
        )

    def get_customer(self, stripe_customer_id: str) -> Optional[Customer]:
        """Retrieve a customer from Stripe."""
        try:
            stripe_customer = stripe.Customer.retrieve(stripe_customer_id)
            return Customer(
                id=stripe_customer.metadata.get("user_id", stripe_customer.id),
                email=stripe_customer.email,
                name=stripe_customer.name,
                stripe_customer_id=stripe_customer.id,
                default_payment_method=stripe_customer.invoice_settings.default_payment_method,
                metadata=dict(stripe_customer.metadata),
            )
        except stripe.error.StripeError:
            return None

    def update_customer(
        self,
        stripe_customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Customer:
        """Update customer details."""
        update_data = {}
        if email:
            update_data["email"] = email
        if name:
            update_data["name"] = name
        if metadata:
            update_data["metadata"] = metadata

        stripe_customer = stripe.Customer.modify(stripe_customer_id, **update_data)

        return Customer(
            id=stripe_customer.metadata.get("user_id", stripe_customer.id),
            email=stripe_customer.email,
            name=stripe_customer.name,
            stripe_customer_id=stripe_customer.id,
            metadata=dict(stripe_customer.metadata),
        )

    # ==================== Subscription Management ====================

    def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        trial_days: int = 0,
        payment_method_id: Optional[str] = None,
    ) -> Subscription:
        """
        Create a new subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            tier: Subscription tier
            trial_days: Number of trial days (0 for no trial)
            payment_method_id: Payment method to use
        """
        price_id = self.get_price_id_for_tier(tier)

        subscription_data = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": {"tier": tier.value},
        }

        if trial_days > 0:
            subscription_data["trial_period_days"] = trial_days

        if payment_method_id:
            subscription_data["default_payment_method"] = payment_method_id

        # For free tier, skip payment requirement
        if tier == SubscriptionTier.FREE:
            subscription_data["payment_behavior"] = "default_incomplete"

        stripe_sub = stripe.Subscription.create(**subscription_data)

        return self._stripe_sub_to_model(stripe_sub)

    def get_subscription(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Retrieve subscription details."""
        try:
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            return self._stripe_sub_to_model(stripe_sub)
        except stripe.error.StripeError:
            return None

    def update_subscription_tier(
        self,
        stripe_subscription_id: str,
        new_tier: SubscriptionTier,
        prorate: bool = True,
    ) -> Subscription:
        """
        Upgrade or downgrade a subscription.

        Args:
            stripe_subscription_id: Current subscription ID
            new_tier: New tier to switch to
            prorate: Whether to prorate the change
        """
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        new_price_id = self.get_price_id_for_tier(new_tier)

        # Update the subscription item
        stripe.Subscription.modify(
            stripe_subscription_id,
            items=[{
                "id": stripe_sub["items"]["data"][0].id,
                "price": new_price_id,
            }],
            proration_behavior="create_prorations" if prorate else "none",
            metadata={"tier": new_tier.value},
        )

        updated_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        return self._stripe_sub_to_model(updated_sub)

    def cancel_subscription(
        self,
        stripe_subscription_id: str,
        at_period_end: bool = True,
    ) -> Subscription:
        """
        Cancel a subscription.

        Args:
            stripe_subscription_id: Subscription to cancel
            at_period_end: If True, cancel at end of billing period
        """
        if at_period_end:
            stripe_sub = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True,
            )
        else:
            stripe_sub = stripe.Subscription.delete(stripe_subscription_id)

        return self._stripe_sub_to_model(stripe_sub)

    def reactivate_subscription(self, stripe_subscription_id: str) -> Subscription:
        """Reactivate a subscription scheduled for cancellation."""
        stripe_sub = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=False,
        )
        return self._stripe_sub_to_model(stripe_sub)

    # ==================== Usage-Based Billing ====================

    def report_usage(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
    ) -> UsageRecord:
        """
        Report API usage for metered billing.

        Args:
            subscription_item_id: The subscription item for metered billing
            quantity: Number of API calls to report
            timestamp: When the usage occurred (defaults to now)
            idempotency_key: Prevent duplicate reporting
        """
        usage_data = {
            "quantity": quantity,
            "action": "increment",
        }

        if timestamp:
            usage_data["timestamp"] = int(timestamp.timestamp())

        kwargs = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            **usage_data,
            **kwargs,
        )

        return UsageRecord(
            id=record.id,
            subscription_id=record.subscription_item,
            quantity=record.quantity,
            timestamp=datetime.fromtimestamp(record.timestamp),
        )

    def get_usage_summary(
        self,
        subscription_item_id: str,
    ) -> dict:
        """Get usage summary for current billing period."""
        records = stripe.SubscriptionItem.list_usage_record_summaries(
            subscription_item_id,
            limit=1,
        )

        if records.data:
            summary = records.data[0]
            return {
                "total_usage": summary.total_usage,
                "period_start": datetime.fromtimestamp(summary.period.start),
                "period_end": datetime.fromtimestamp(summary.period.end),
            }

        return {"total_usage": 0, "period_start": None, "period_end": None}

    # ==================== Payment Methods ====================

    def create_setup_intent(self, customer_id: str) -> dict:
        """Create a SetupIntent for adding a payment method."""
        intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=["card"],
        )
        return {
            "client_secret": intent.client_secret,
            "setup_intent_id": intent.id,
        }

    def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str,
        set_default: bool = True,
    ) -> str:
        """Attach a payment method to a customer."""
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)

        if set_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

        return payment_method_id

    def list_payment_methods(self, customer_id: str) -> list[dict]:
        """List customer's payment methods."""
        methods = stripe.PaymentMethod.list(customer=customer_id, type="card")
        return [
            {
                "id": pm.id,
                "brand": pm.card.brand,
                "last4": pm.card.last4,
                "exp_month": pm.card.exp_month,
                "exp_year": pm.card.exp_year,
            }
            for pm in methods.data
        ]

    # ==================== Invoices ====================

    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[Invoice]:
        """List customer invoices."""
        invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
        return [self._stripe_invoice_to_model(inv) for inv in invoices.data]

    def get_upcoming_invoice(self, customer_id: str) -> Optional[Invoice]:
        """Get the upcoming invoice for a customer."""
        try:
            invoice = stripe.Invoice.upcoming(customer=customer_id)
            return self._stripe_invoice_to_model(invoice)
        except stripe.error.InvalidRequestError:
            return None

    # ==================== Webhooks ====================

    def construct_webhook_event(
        self,
        payload: bytes,
        signature: str,
    ) -> stripe.Event:
        """
        Verify and construct a webhook event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Verified Stripe event
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        return stripe.Webhook.construct_event(
            payload,
            signature,
            self.webhook_secret,
        )

    def handle_webhook_event(self, event: stripe.Event) -> dict:
        """
        Process a webhook event.

        Returns action to take based on event type.
        """
        event_type = event.type
        data = event.data.object

        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.created": self._handle_customer_created,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        return {"action": "ignored", "event_type": event_type}

    # ==================== Checkout Sessions ====================

    def create_checkout_session(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        """Create a Stripe Checkout session for subscription."""
        # Get price ID (fetches from product if not in env)
        price_id = self.get_price_id_for_tier(tier)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"tier": tier.value},
        )

        return {
            "session_id": session.id,
            "url": session.url,
        }

    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> dict:
        """Create a Stripe Billing Portal session."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return {"url": session.url}

    # ==================== Helper Methods ====================

    def _stripe_sub_to_model(self, stripe_sub) -> Subscription:
        """Convert Stripe subscription to our model."""
        return Subscription(
            id=stripe_sub.metadata.get("user_id", stripe_sub.id),
            customer_id=stripe_sub.customer,
            stripe_subscription_id=stripe_sub.id,
            tier=stripe_sub.metadata.get("tier", "free"),
            status=SubscriptionStatus(stripe_sub.status),
            current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
            cancel_at_period_end=stripe_sub.cancel_at_period_end,
            canceled_at=datetime.fromtimestamp(stripe_sub.canceled_at) if stripe_sub.canceled_at else None,
            trial_end=datetime.fromtimestamp(stripe_sub.trial_end) if stripe_sub.trial_end else None,
            metadata=dict(stripe_sub.metadata),
        )

    def _stripe_invoice_to_model(self, stripe_inv) -> Invoice:
        """Convert Stripe invoice to our model."""
        return Invoice(
            id=stripe_inv.id,
            customer_id=stripe_inv.customer,
            stripe_invoice_id=stripe_inv.id,
            subscription_id=stripe_inv.subscription,
            amount_due=stripe_inv.amount_due,
            amount_paid=stripe_inv.amount_paid,
            currency=stripe_inv.currency,
            status=PaymentStatus(stripe_inv.status) if stripe_inv.status else PaymentStatus.DRAFT,
            invoice_pdf=stripe_inv.invoice_pdf,
            hosted_invoice_url=stripe_inv.hosted_invoice_url,
            period_start=datetime.fromtimestamp(stripe_inv.period_start) if stripe_inv.period_start else None,
            period_end=datetime.fromtimestamp(stripe_inv.period_end) if stripe_inv.period_end else None,
        )

    # Webhook handlers
    def _handle_subscription_created(self, data) -> dict:
        return {
            "action": "subscription_created",
            "subscription_id": data.id,
            "customer_id": data.customer,
            "tier": data.metadata.get("tier", "free"),
        }

    def _handle_subscription_updated(self, data) -> dict:
        return {
            "action": "subscription_updated",
            "subscription_id": data.id,
            "status": data.status,
            "tier": data.metadata.get("tier", "free"),
        }

    def _handle_subscription_deleted(self, data) -> dict:
        return {
            "action": "subscription_deleted",
            "subscription_id": data.id,
            "customer_id": data.customer,
        }

    def _handle_invoice_paid(self, data) -> dict:
        return {
            "action": "invoice_paid",
            "invoice_id": data.id,
            "customer_id": data.customer,
            "amount_paid": data.amount_paid,
        }

    def _handle_payment_failed(self, data) -> dict:
        return {
            "action": "payment_failed",
            "invoice_id": data.id,
            "customer_id": data.customer,
            "attempt_count": data.attempt_count,
        }

    def _handle_customer_created(self, data) -> dict:
        return {
            "action": "customer_created",
            "customer_id": data.id,
            "email": data.email,
        }
