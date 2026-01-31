"""
Billing API Routes - Stripe subscription and payment management.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from api.auth import get_current_user
from db.models import User
from quantumflow.billing import (
    StripeService,
    SubscriptionTier,
    TIER_PRICES,
    TIER_LIMITS,
)

router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize Stripe service (lazy init to handle missing keys gracefully)
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get or create Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service


# ==================== Request/Response Models ====================


class CreateCustomerRequest(BaseModel):
    """Request to create a Stripe customer."""
    email: str
    name: Optional[str] = None


class CreateSubscriptionRequest(BaseModel):
    """Request to create a subscription."""
    tier: SubscriptionTier
    payment_method_id: Optional[str] = None
    trial_days: int = 0


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription tier."""
    tier: SubscriptionTier
    prorate: bool = True


class CheckoutSessionRequest(BaseModel):
    """Request to create checkout session."""
    tier: SubscriptionTier
    success_url: str
    cancel_url: str


class BillingPortalRequest(BaseModel):
    """Request for billing portal session."""
    return_url: str


class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    id: str
    tier: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    trial_end: Optional[datetime] = None


class PricingResponse(BaseModel):
    """Pricing information response."""
    tier: str
    monthly_price: float
    api_calls_included: int
    overage_price_per_call: float
    features: dict


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    amount_due: float
    amount_paid: float
    currency: str
    status: str
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""
    total_usage: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    tier: str
    limit: int
    remaining: int
    overage: int


# ==================== Pricing Endpoints ====================


@router.get("/pricing", response_model=list[PricingResponse])
async def get_pricing():
    """Get pricing information for all tiers."""
    pricing = []
    for tier in SubscriptionTier:
        price_info = TIER_PRICES[tier]
        tier_limits = TIER_LIMITS[tier]
        pricing.append(PricingResponse(
            tier=tier.value,
            monthly_price=price_info.monthly_price_dollars,
            api_calls_included=price_info.api_calls_included,
            overage_price_per_call=price_info.overage_price_per_call,
            features=tier_limits,
        ))
    return pricing


# ==================== Customer Endpoints ====================


@router.post("/customers")
async def create_customer(
    request: CreateCustomerRequest,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Create a Stripe customer for the current user."""
    try:
        customer = stripe.create_customer(
            email=request.email,
            name=request.name,
            user_id=str(current_user.id),
            metadata={"user_id": str(current_user.id)},
        )
        return {
            "customer_id": customer.stripe_customer_id,
            "email": customer.email,
            "name": customer.name,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers/me")
async def get_current_customer(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Get current user's Stripe customer details."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing account found")

    customer = stripe.get_customer(stripe_customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "customer_id": customer.stripe_customer_id,
        "email": customer.email,
        "name": customer.name,
        "has_payment_method": customer.has_payment_method,
    }


# ==================== Subscription Endpoints ====================


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Create a new subscription."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="Create a billing account first"
        )

    try:
        subscription = stripe.create_subscription(
            customer_id=stripe_customer_id,
            tier=request.tier,
            trial_days=request.trial_days,
            payment_method_id=request.payment_method_id,
        )
        return SubscriptionResponse(
            id=subscription.stripe_subscription_id,
            tier=subscription.tier,
            status=subscription.status.value,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            trial_end=subscription.trial_end,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Get current user's active subscription."""
    subscription_id = getattr(current_user, 'stripe_subscription_id', None)
    if not subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription")

    subscription = stripe.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return SubscriptionResponse(
        id=subscription.stripe_subscription_id,
        tier=subscription.tier,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription.trial_end,
    )


@router.patch("/subscriptions/current", response_model=SubscriptionResponse)
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Update subscription tier (upgrade/downgrade)."""
    subscription_id = getattr(current_user, 'stripe_subscription_id', None)
    if not subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription")

    try:
        subscription = stripe.update_subscription_tier(
            stripe_subscription_id=subscription_id,
            new_tier=request.tier,
            prorate=request.prorate,
        )
        return SubscriptionResponse(
            id=subscription.stripe_subscription_id,
            tier=subscription.tier,
            status=subscription.status.value,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subscriptions/current")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Cancel current subscription."""
    subscription_id = getattr(current_user, 'stripe_subscription_id', None)
    if not subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription")

    try:
        subscription = stripe.cancel_subscription(
            stripe_subscription_id=subscription_id,
            at_period_end=at_period_end,
        )
        return {
            "message": "Subscription cancelled",
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "current_period_end": subscription.current_period_end,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/current/reactivate")
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Reactivate a cancelled subscription."""
    subscription_id = getattr(current_user, 'stripe_subscription_id', None)
    if not subscription_id:
        raise HTTPException(status_code=404, detail="No subscription found")

    try:
        subscription = stripe.reactivate_subscription(subscription_id)
        return {
            "message": "Subscription reactivated",
            "status": subscription.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Usage Endpoints ====================


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Get usage summary for current billing period."""
    subscription_item_id = getattr(current_user, 'stripe_subscription_item_id', None)
    tier = getattr(current_user, 'tier', 'free')
    tier_enum = SubscriptionTier(tier)
    limit = TIER_LIMITS[tier_enum]["api_calls_monthly"]

    if subscription_item_id:
        summary = stripe.get_usage_summary(subscription_item_id)
        total_usage = summary["total_usage"]
    else:
        # For free tier or no subscription, use internal tracking
        total_usage = 0  # Would come from usage tracking
        summary = {"period_start": None, "period_end": None}

    return UsageSummaryResponse(
        total_usage=total_usage,
        period_start=summary.get("period_start"),
        period_end=summary.get("period_end"),
        tier=tier,
        limit=limit,
        remaining=max(0, limit - total_usage),
        overage=max(0, total_usage - limit),
    )


# ==================== Payment Methods ====================


@router.post("/payment-methods/setup")
async def create_setup_intent(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Create a SetupIntent for adding a payment method."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="Create billing account first")

    intent = stripe.create_setup_intent(stripe_customer_id)
    return intent


@router.get("/payment-methods")
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """List saved payment methods."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        return []

    methods = stripe.list_payment_methods(stripe_customer_id)
    return methods


# ==================== Invoices ====================


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """List invoices for current user."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        return []

    invoices = stripe.list_invoices(stripe_customer_id, limit=limit)
    return [
        InvoiceResponse(
            id=inv.stripe_invoice_id,
            amount_due=inv.amount_due_dollars,
            amount_paid=inv.amount_paid_dollars,
            currency=inv.currency,
            status=inv.status.value,
            invoice_pdf=inv.invoice_pdf,
            hosted_invoice_url=inv.hosted_invoice_url,
            period_start=inv.period_start,
            period_end=inv.period_end,
        )
        for inv in invoices
    ]


@router.get("/invoices/upcoming", response_model=Optional[InvoiceResponse])
async def get_upcoming_invoice(
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Get upcoming invoice preview."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        return None

    invoice = stripe.get_upcoming_invoice(stripe_customer_id)
    if not invoice:
        return None

    return InvoiceResponse(
        id=invoice.stripe_invoice_id,
        amount_due=invoice.amount_due_dollars,
        amount_paid=invoice.amount_paid_dollars,
        currency=invoice.currency,
        status=invoice.status.value,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
    )


# ==================== Checkout & Portal ====================


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Create a Stripe Checkout session."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)

    # Auto-create customer if not exists
    if not stripe_customer_id:
        email = current_user.email
        if not email:
            raise HTTPException(status_code=400, detail="User email required")

        customer = stripe.create_customer(
            email=email,
            name=current_user.name,
            user_id=str(current_user.id),
            metadata={"user_id": str(current_user.id)},
        )
        stripe_customer_id = customer.stripe_customer_id
        # Note: In production, save stripe_customer_id to user record in database

    try:
        session = stripe.create_checkout_session(
            customer_id=stripe_customer_id,
            tier=request.tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
async def create_billing_portal(
    request: BillingPortalRequest,
    current_user: User = Depends(get_current_user),
    stripe: StripeService = Depends(get_stripe_service),
):
    """Create a Stripe Billing Portal session."""
    stripe_customer_id = getattr(current_user, 'stripe_customer_id', None)
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account")

    session = stripe.create_billing_portal_session(
        customer_id=stripe_customer_id,
        return_url=request.return_url,
    )
    return session


# ==================== Webhooks ====================


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        stripe_service = get_stripe_service()
        payload = await request.body()
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
        result = stripe_service.handle_webhook_event(event)

        # TODO: Update database based on result
        # - subscription_created -> update user tier
        # - subscription_deleted -> downgrade to free
        # - payment_failed -> send notification

        return {"received": True, "action": result.get("action")}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")
