"""Billing service — Stripe integration for subscription management."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models import User

logger = logging.getLogger(__name__)

TIERS = {
    "free": {"price": 0, "msg_per_day": 5, "tools": "basic"},
    "pro": {"price": 500, "msg_per_day": 100, "tools": "all"},  # cents ($5)
    "pro_plus": {"price": 1500, "msg_per_day": -1, "tools": "all"},  # cents ($15)
}

STRIPE_PRICE_MAP = {
    "pro": "price_pro_monthly",  # Replace with actual Stripe price ID
    "pro_plus": "price_pro_plus_monthly",
}


def _get_stripe():
    """Lazy import Stripe to avoid crash if not configured."""
    if not settings.STRIPE_SECRET_KEY:
        return None
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


async def create_checkout_session(
    user_id: str, tier: str, db: AsyncSession,
) -> str | None:
    """Create Stripe Checkout session. Returns checkout URL."""
    stripe = _get_stripe()
    if not stripe:
        return None

    user = await db.get(User, UUID(user_id))
    if not user:
        return None

    price_id = STRIPE_PRICE_MAP.get(tier)
    if not price_id:
        return None

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"https://{settings.DOMAIN}/settings?upgraded=1",
        cancel_url=f"https://{settings.DOMAIN}/settings",
        client_reference_id=user_id,
        customer_email=user.email,
        metadata={"user_id": user_id, "tier": tier},
    )
    return session.url


async def handle_webhook_event(payload: bytes, sig: str) -> bool:
    """Process Stripe webhook event. Returns True if handled."""
    stripe = _get_stripe()
    if not stripe:
        return False

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        logger.warning("Stripe webhook signature failed")
        return False

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id")
        tier = session.get("metadata", {}).get("tier", "pro")
        if user_id:
            from db.session import async_session
            async with async_session() as db:
                user = await db.get(User, UUID(user_id))
                if user:
                    user.tier = tier
                    await db.commit()
                    logger.info(f"User {user_id} upgraded to {tier}")

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        # Find user by Stripe customer ID
        customer_email = sub.get("customer_email", "")
        if customer_email:
            from db.session import async_session
            async with async_session() as db:
                user = (await db.execute(
                    select(User).where(User.email == customer_email)
                )).scalar_one_or_none()
                if user:
                    user.tier = "free"
                    await db.commit()
                    logger.info(f"User {user.id} downgraded to free")

    return True
