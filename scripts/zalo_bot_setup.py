#!/usr/bin/env python3
"""Set webhook URL for Zalo Bot Platform.

Usage:
    python scripts/zalo_bot_setup.py https://api.your-domain.com/api/v1/webhooks/zalo-bot
"""
import sys
import httpx
import os

BOT_TOKEN = os.environ.get("ZALO_BOT_TOKEN", "")
SECRET_TOKEN = os.environ.get("ZALO_BOT_SECRET_TOKEN", "")
API = f"https://bot-api.zaloplatforms.com/bot{BOT_TOKEN}"


def main():
    if not BOT_TOKEN:
        print("❌ ZALO_BOT_TOKEN not set")
        sys.exit(1)

    if len(sys.argv) < 2:
        # No URL = show bot info
        r = httpx.get(f"{API}/getMe")
        print(r.json())
        return

    url = sys.argv[1]
    body = {"url": url}
    if SECRET_TOKEN:
        body["secret_token"] = SECRET_TOKEN

    r = httpx.post(f"{API}/setWebhook", json=body)
    data = r.json()
    if data.get("ok"):
        print(f"✅ Webhook set: {url}")
    else:
        print(f"❌ Failed: {data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
