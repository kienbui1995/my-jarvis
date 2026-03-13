"""Feedback collection for early testers."""
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from core.deps import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()


class FeedbackIn(BaseModel):
    message_id: str
    rating: str
    comment: str = ""


@router.post("/feedback")
async def submit_feedback(body: FeedbackIn, user_id: str = Depends(get_current_user_id)):
    logger.info("feedback user=%s message=%s rating=%s", user_id, body.message_id, body.rating)
    return {"ok": True}
