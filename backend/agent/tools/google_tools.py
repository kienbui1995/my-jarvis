"""Google integration tools — Calendar + Gmail via OAuth2."""
from datetime import datetime, timedelta
from typing import Annotated

import httpx
from langchain_core.tools import InjectedToolArg, tool

from db.session import async_session
from services.google_oauth import get_valid_token

CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GMAIL_API = "https://www.googleapis.com/gmail/v1"


async def _get_google_client(user_id: str) -> tuple[str | None, str]:
    """Get valid Google token for user. Returns (token, error_msg)."""
    async with async_session() as db:
        token = await get_valid_token(user_id, db)
    if not token:
        return None, (
            "Chưa kết nối Google. Vào Settings > Kết nối > Google để liên kết."
        )
    return token, ""


# ── Google Calendar ──────────────────────────────────────────

@tool
async def google_calendar_list(
    days: int = 7,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Xem lịch Google Calendar. Args: days (số ngày, mặc định 7)."""
    token, err = await _get_google_client(user_id)
    if not token:
        return err

    now = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": now, "timeMax": end,
                "singleEvents": "true", "orderBy": "startTime",
                "maxResults": "15",
            },
        )
        if resp.status_code == 401:
            return "Token Google hết hạn. Vui lòng kết nối lại."
        if resp.status_code != 200:
            return f"Lỗi Google Calendar (HTTP {resp.status_code})"
        data = resp.json()

    events = data.get("items", [])
    if not events:
        return f"📅 Không có sự kiện nào trong {days} ngày tới trên Google Calendar."

    lines = [f"📅 Google Calendar ({len(events)} sự kiện):"]
    for e in events:
        start = e.get("start", {})
        dt = start.get("dateTime", start.get("date", ""))
        if "T" in dt:
            dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            time_str = dt_obj.strftime("%d/%m %H:%M")
        else:
            time_str = dt
        loc = e.get("location", "")
        lines.append(f"  - {time_str} {e.get('summary', '(no title)')}"
                      + (f" @ {loc}" if loc else ""))
    return "\n".join(lines)


# ── Gmail ────────────────────────────────────────────────────

@tool
async def gmail_read(
    max_results: int = 5,
    query: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Đọc email gần đây từ Gmail.

    Args:
        max_results: số email tối đa (mặc định 5)
        query: tìm kiếm (ví dụ: "from:boss" hoặc "subject:invoice"). Để trống = inbox mới nhất.
    """
    token, err = await _get_google_client(user_id)
    if not token:
        return err

    headers = {"Authorization": f"Bearer {token}"}
    params = {"maxResults": str(min(max_results, 10))}
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=10) as client:
        # List message IDs
        resp = await client.get(
            f"{GMAIL_API}/users/me/messages",
            headers=headers, params=params,
        )
        if resp.status_code != 200:
            return f"Lỗi Gmail (HTTP {resp.status_code})"
        msg_list = resp.json().get("messages", [])

        if not msg_list:
            return "📧 Không có email mới."

        # Fetch each message metadata
        lines = ["📧 Email gần đây:"]
        for msg_ref in msg_list[:max_results]:
            msg_resp = await client.get(
                f"{GMAIL_API}/users/me/messages/{msg_ref['id']}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": "From,Subject,Date"},
            )
            if msg_resp.status_code != 200:
                continue
            msg_data = msg_resp.json()
            hdrs = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            subj = hdrs.get("Subject", "(no subject)")
            frm = hdrs.get("From", "")
            # Shorten "Name <email>" to just "Name"
            if "<" in frm:
                frm = frm.split("<")[0].strip().strip('"')
            lines.append(f"  - {frm}: {subj}")

    return "\n".join(lines)


@tool
async def gmail_send(
    to: str,
    subject: str,
    body: str,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Gửi email qua Gmail. Args: to (địa chỉ email), subject, body."""
    token, err = await _get_google_client(user_id)
    if not token:
        return err

    import base64
    raw_msg = (
        f"To: {to}\r\nSubject: {subject}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n{body}"
    )
    encoded = base64.urlsafe_b64encode(raw_msg.encode()).decode()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GMAIL_API}/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"raw": encoded},
        )
        if resp.status_code != 200:
            return f"Gửi email thất bại (HTTP {resp.status_code})"

    return f"✉️ Đã gửi email đến {to}: \"{subject}\""
