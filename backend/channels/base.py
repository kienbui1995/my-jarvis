from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JarvisMessage:
    """Unified internal message format across all channels."""
    user_id: str
    channel: str  # "zalo" | "telegram" | "web"
    content: str
    attachments: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JarvisResponse:
    """Unified response format."""
    content: str
    attachments: list[dict] = field(default_factory=list)
    quick_replies: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ChannelAdapter(ABC):
    """Base class for all channel adapters."""

    @abstractmethod
    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        """Normalize platform-specific payload into JarvisMessage."""
        ...

    @abstractmethod
    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        """Send JarvisResponse back via platform API."""
        ...

    @abstractmethod
    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        """Verify webhook signature/authenticity."""
        ...
