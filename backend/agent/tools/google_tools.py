"""Google integration tools — Calendar + Gmail via OAuth2."""
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
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
    read_body: bool = False,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Đọc email gần đây từ Gmail.

    Args:
        max_results: số email tối đa (mặc định 5)
        query: tìm kiếm (ví dụ: "from:boss" hoặc "subject:invoice"). Để trống = inbox mới nhất.
        read_body: True để đọc nội dung email (chỉ email đầu tiên), False để liệt kê tiêu đề.
    """
    token, err = await _get_google_client(user_id)
    if not token:
        return err

    headers = {"Authorization": f"Bearer {token}"}
    params = {"maxResults": str(min(max_results, 10))}
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GMAIL_API}/users/me/messages",
            headers=headers, params=params,
        )
        if resp.status_code != 200:
            return f"Lỗi Gmail (HTTP {resp.status_code})"
        msg_list = resp.json().get("messages", [])

        if not msg_list:
            return "📧 Không có email mới."

        # Read full body of first email
        if read_body:
            msg_resp = await client.get(
                f"{GMAIL_API}/users/me/messages/{msg_list[0]['id']}",
                headers=headers, params={"format": "full"},
            )
            if msg_resp.status_code != 200:
                return "Không đọc được email."
            return _format_full_email(msg_resp.json())

        # List mode — show subject + from
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
            if "<" in frm:
                frm = frm.split("<")[0].strip().strip('"')
            lines.append(f"  - {frm}: {subj}")

    return "\n".join(lines)


def _extract_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text
    return ""


def _format_full_email(msg_data: dict) -> str:
    hdrs = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
    frm = hdrs.get("From", "")
    subj = hdrs.get("Subject", "(no subject)")
    date = hdrs.get("Date", "")
    body = _extract_body(msg_data.get("payload", {}))[:2000]
    return f"📧 Email:\nTừ: {frm}\nTiêu đề: {subj}\nNgày: {date}\n\n{body}"


@tool
async def gmail_reply(
    message_query: str,
    reply_body: str,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Trả lời email. Tìm email gần nhất khớp query rồi reply.

    Args:
        message_query: tìm email cần reply (ví dụ: "from:boss subject:báo cáo")
        reply_body: nội dung reply
    """
    token, err = await _get_google_client(user_id)
    if not token:
        return err

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        # Find the email
        resp = await client.get(
            f"{GMAIL_API}/users/me/messages",
            headers=headers, params={"maxResults": "1", "q": message_query},
        )
        if resp.status_code != 200:
            return f"Lỗi Gmail (HTTP {resp.status_code})"
        msgs = resp.json().get("messages", [])
        if not msgs:
            return "Không tìm thấy email để reply."

        # Get original message
        msg_resp = await client.get(
            f"{GMAIL_API}/users/me/messages/{msgs[0]['id']}",
            headers=headers, params={"format": "metadata", "metadataHeaders": "From,Subject,Message-ID"},
        )
        if msg_resp.status_code != 200:
            return "Không đọc được email gốc."
        msg_data = msg_resp.json()
        hdrs = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        to = hdrs.get("From", "")
        subj = hdrs.get("Subject", "")
        msg_id = hdrs.get("Message-ID", "")
        thread_id = msg_data.get("threadId", "")
        if not subj.lower().startswith("re:"):
            subj = f"Re: {subj}"

        msg = MIMEText(reply_body, "plain", "utf-8")
        msg["To"] = to
        msg["Subject"] = subj
        msg["In-Reply-To"] = msg_id
        msg["References"] = msg_id
        encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        resp = await client.post(
            f"{GMAIL_API}/users/me/messages/send",
            headers={**headers, "Content-Type": "application/json"},
            json={"raw": encoded, "threadId": thread_id},
        )
        if resp.status_code != 200:
            return f"Reply thất bại (HTTP {resp.status_code})"

    return f"✉️ Đã reply đến {to}: \"{subj}\""


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

    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["Subject"] = subject
    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()

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
