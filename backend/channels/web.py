from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse


class WebSocketAdapter(ChannelAdapter):
    """WebSocket adapter for web dashboard — messages handled via FastAPI WebSocket endpoint."""

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        return JarvisMessage(
            user_id=raw_payload["user_id"],
            channel="web",
            content=raw_payload.get("content", ""),
            attachments=raw_payload.get("attachments", []),
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        # WebSocket send is handled directly in the WS endpoint, not here
        pass

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        return True  # WS auth handled via JWT on connection
