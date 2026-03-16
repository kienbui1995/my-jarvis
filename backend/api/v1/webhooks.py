"""Webhook endpoints for Zalo, Telegram, WhatsApp, Slack, Discord."""
import logging

from fastapi import APIRouter, BackgroundTasks, Query, Request
from langchain_core.messages import HumanMessage

from agent.graph import get_jarvis_graph
from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from channels.discord import DiscordAdapter
from channels.slack import SlackAdapter
from channels.telegram import TelegramAdapter
from channels.whatsapp import WhatsAppAdapter
from channels.zalo import ZaloAdapter
from channels.zalo_bot import ZaloBotAdapter
from core.config import settings
from db.session import async_session
from memory.conversation_memory import build_memory_context, summarize_if_needed
from memory.preference_learning import build_preference_prompt
from services.conversation import get_or_create_conversation, load_history, save_message
from services.user import get_or_create_user

logger = logging.getLogger(__name__)
router = APIRouter()
zalo = ZaloAdapter()
zalo_bot = ZaloBotAdapter()
telegram = TelegramAdapter()
whatsapp = WhatsAppAdapter()
slack = SlackAdapter()
discord = DiscordAdapter()


def _resolve_user_kwargs(msg: JarvisMessage) -> dict:
    """Map channel to get_or_create_user kwargs."""
    name = msg.metadata.get("display_name", "")
    if msg.channel == "zalo":
        return {"zalo_id": msg.user_id, "name": name}
    if msg.channel == "zalo_bot":
        return {"zalo_bot_id": msg.user_id, "name": name}
    if msg.channel == "telegram":
        return {"telegram_id": msg.user_id, "name": name}
    if msg.channel == "whatsapp":
        return {"whatsapp_id": msg.user_id, "name": name}
    if msg.channel == "slack":
        return {"slack_id": msg.user_id, "name": name}
    if msg.channel == "discord":
        return {"discord_id": msg.user_id, "name": name}
    return {}


async def _try_link_code(adapter: ChannelAdapter, msg: JarvisMessage) -> bool:
    """Handle /link <code> command. Returns True if handled."""
    text = msg.content.strip()
    if not text.startswith("/link"):
        return False
    parts = text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        recipient = msg.metadata.get("chat_id") or msg.user_id
        await adapter.send_response(str(recipient), JarvisResponse(content="Dùng: /link <mã 6 số> (lấy mã từ Settings > Kết nối trên web)"))
        return True

    code = parts[1]
    from llm.budget import get_redis
    redis = await get_redis()
    web_user_id = await redis.get(f"link:{code}")
    if not web_user_id:
        recipient = msg.metadata.get("chat_id") or msg.user_id
        await adapter.send_response(str(recipient), JarvisResponse(content="Mã không hợp lệ hoặc đã hết hạn. Vui lòng tạo mã mới."))
        return True

    # Link channel account to web user
    field_map = {"telegram": "telegram_id", "zalo": "zalo_id", "zalo_bot": "zalo_bot_id"}
    field = field_map.get(msg.channel)
    if not field:
        return True

    async with async_session() as db:
        from db.models import User
        user = await db.get(User, web_user_id.decode() if isinstance(web_user_id, bytes) else web_user_id)
        if user:
            setattr(user, field, msg.user_id)
            await db.commit()
            await redis.delete(f"link:{code}")
            recipient = msg.metadata.get("chat_id") or msg.user_id
            await adapter.send_response(str(recipient), JarvisResponse(content=f"✅ Đã liên kết thành công! Xin chào {user.name or 'bạn'} 👋"))
        else:
            recipient = msg.metadata.get("chat_id") or msg.user_id
            await adapter.send_response(str(recipient), JarvisResponse(content="Không tìm thấy tài khoản."))
    return True


async def _process_message(adapter: ChannelAdapter, msg: JarvisMessage) -> None:
    """Full pipeline: resolve user → invoke agent graph → send response."""
    try:
        # Handle /link command before AI
        if await _try_link_code(adapter, msg):
            return

        async with async_session() as db:
            user = await get_or_create_user(db, **_resolve_user_kwargs(msg))
            if not user:
                return
            conv = await get_or_create_conversation(db, user.id, msg.channel)
            await save_message(db, conv.id, "user", msg.content)
            history = await load_history(db, conv.id, limit=20)
            convo_ctx = await build_memory_context(conv.id, db)
            pref_ctx = await build_preference_prompt(str(user.id), db)

        graph = await get_jarvis_graph()
        user_pref_combined = "\n".join(filter(None, [pref_ctx, convo_ctx]))
        config = {"configurable": {"thread_id": str(conv.id)}}
        result = await graph.ainvoke({
            "messages": history + [HumanMessage(content=msg.content)],
            "user_id": str(user.id),
            "user_tier": user.tier,
            "channel": msg.channel,
            "conversation_id": str(conv.id),
            "user_preferences": user_pref_combined,
        }, config=config)

        response_text = result.get("final_response", "Xin lỗi, tôi không thể xử lý yêu cầu này.")

        async with async_session() as db:
            await save_message(db, conv.id, "assistant", response_text,
                               model_used=result.get("selected_model", ""))
            await summarize_if_needed(conv.id, db)

        # Reply to chat_id for channels that support group chat
        recipient = msg.metadata.get("chat_id") or msg.user_id
        resp = JarvisResponse(
            content=response_text,
            quick_replies=result.get("zalo_quick_replies", []) if msg.channel == "zalo" else [],
        )
        await adapter.send_response(str(recipient), resp)

    except Exception:
        logger.exception(f"Failed to process message from {msg.channel}:{msg.user_id}")


# --- Zalo OA ---

@router.post("/zalo")
async def zalo_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()
    if not await zalo.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid signature"}

    event = payload.get("event_name", "")
    if event in ("follow", "user_submit_info"):
        sender_id = payload.get("follower", {}).get("id") or payload.get("sender", {}).get("id", "")
        if sender_id:
            bg.add_task(_handle_follow, sender_id)
        return {"status": "ok"}

    msg = await zalo.parse_incoming(payload)
    if msg.content:
        bg.add_task(_process_message, zalo, msg)
    return {"status": "ok"}


async def _handle_follow(zalo_user_id: str):
    try:
        async with async_session() as db:
            await get_or_create_user(db, zalo_id=zalo_user_id)
        await zalo.send_greeting(zalo_user_id)
    except Exception:
        logger.exception(f"Follow handling failed for {zalo_user_id}")


# --- Zalo Bot Platform ---

@router.post("/zalo-bot")
async def zalo_bot_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()
    if not await zalo_bot.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid token"}
    msg = await zalo_bot.parse_incoming(payload)
    event = msg.metadata.get("event", "")
    chat_id = msg.metadata.get("chat_id") or msg.user_id

    if msg.content:
        # Text or image with caption → process with AI
        bg.add_task(_process_message, zalo_bot, msg)
    elif event == "message.sticker.received":
        # Sticker → friendly ack, no AI needed
        bg.add_task(zalo_bot.send_response, chat_id, JarvisResponse(content="😄"))
    elif event == "message.unsupported.received":
        # Protected user → polite decline
        bg.add_task(zalo_bot.send_response, chat_id,
                    JarvisResponse(content="Xin lỗi, tôi chưa thể xử lý tin nhắn này."))

    return {"status": "ok"}


# --- Telegram ---

@router.post("/telegram")
async def telegram_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()
    if not await telegram.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid signature"}
    msg = await telegram.parse_incoming(payload)
    if msg.content:
        bg.add_task(_process_message, telegram, msg)
    return {"status": "ok"}


# --- WhatsApp ---

@router.get("/whatsapp")
async def whatsapp_verify(
    mode: str = Query("", alias="hub.mode"),
    token: str = Query("", alias="hub.verify_token"),
    challenge: str = Query("", alias="hub.challenge"),
):
    """WhatsApp webhook verification (GET)."""
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(challenge)
    return {"error": "verification failed"}


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()
    if not await whatsapp.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid signature"}
    msg = await whatsapp.parse_incoming(payload)
    if msg.content and msg.user_id:
        bg.add_task(_process_message, whatsapp, msg)
    return {"status": "ok"}


# --- Slack ---

@router.post("/slack")
async def slack_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()

    # Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    if not await slack.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid signature"}

    event = payload.get("event", {})
    # Ignore bot messages to prevent loops
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return {"status": "ok"}

    msg = await slack.parse_incoming(payload)
    if msg.content and msg.user_id:
        bg.add_task(_process_message, slack, msg)
    return {"status": "ok"}


# --- Discord ---

@router.post("/discord")
async def discord_webhook(request: Request, bg: BackgroundTasks):
    payload = await request.json()
    if not await discord.verify_webhook(payload, dict(request.headers)):
        return {"error": "invalid signature"}

    # Discord ping (type 1) — must respond with type 1
    if payload.get("type") == 1:
        return {"type": 1}

    msg = await discord.parse_incoming(payload)
    if msg.content and msg.user_id:
        # For interactions, send deferred response first
        if payload.get("token"):
            await discord.send_interaction_response(
                payload["id"], payload["token"],
                "Đang suy nghĩ... 🤔",
            )
        bg.add_task(_process_message, discord, msg)
    return {"status": "ok"}
