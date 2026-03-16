"""Billing API — Stripe checkout + webhook."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user_id, get_db
from services.billing import TIERS, create_checkout_session, handle_webhook_event

router = APIRouter()


class CheckoutRequest(BaseModel):
    tier: str  # "pro" or "pro_plus"


@router.get("/plans")
async def list_plans():
    return {"plans": TIERS}


@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(501, "Billing not configured")
    if body.tier not in ("pro", "pro_plus"):
        raise HTTPException(400, "Invalid tier")
    url = await create_checkout_session(user_id, body.tier, db)
    if not url:
        raise HTTPException(500, "Failed to create checkout")
    return {"url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    handled = await handle_webhook_event(payload, sig)
    return {"ok": handled}
