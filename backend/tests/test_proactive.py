"""Tests for M14 Event-driven Proactive Engine."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import settings

settings.PROACTIVE_ENGINE_ENABLED = True


class TestEventBus:
    @pytest.mark.asyncio
    async def test_emit_publishes_to_stream(self):
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        with patch("services.event_bus.redis_pool") as pool:
            pool.get.return_value = mock_redis
            from services.event_bus import emit
            result = await emit("task.created", "user-1", {"task_id": "t1"})
            assert result == "1-0"
            mock_redis.xadd.assert_called_once()
            call_args = mock_redis.xadd.call_args
            assert call_args[0][0] == "jarvis:events"
            event_data = call_args[0][1]
            assert event_data["type"] == "task.created"
            assert event_data["user_id"] == "user-1"
            assert json.loads(event_data["payload"])["task_id"] == "t1"

    @pytest.mark.asyncio
    async def test_emit_returns_none_on_error(self):
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(side_effect=Exception("Redis down"))
        with patch("services.event_bus.redis_pool") as pool:
            pool.get.return_value = mock_redis
            from services.event_bus import emit
            result = await emit("task.created", "user-1", {})
            assert result is None


class TestTriggerEngine:
    """Trigger engine tests — require pgvector (Docker only)."""

    @pytest.mark.asyncio
    async def test_register_handler(self, client):
        from services.trigger_engine import (
            TriggerHandler,
            get_all_trigger_types,
            get_handlers_for_event,
            register_handler,
        )

        @register_handler
        class TestHandler(TriggerHandler):
            TRIGGER_TYPE = "test_trigger"
            LISTENS_TO = ["test.event"]

            async def should_fire(self, event, trigger, db):
                return True

            async def build_message(self, event, trigger, db):
                return "test message"

        assert "test_trigger" in get_all_trigger_types()
        handlers = get_handlers_for_event("test.event")
        assert any(h.TRIGGER_TYPE == "test_trigger" for h in handlers)

    @pytest.mark.asyncio
    async def test_builtin_handlers_registered(self, client):
        import services.handlers  # noqa: F401
        from services.trigger_engine import get_handlers_for_event

        assert len(get_handlers_for_event("task.created")) > 0
        assert len(get_handlers_for_event("expense.created")) > 0
        assert len(get_handlers_for_event("calendar.created")) > 0
        assert len(get_handlers_for_event("conversation.ended")) > 0
        assert len(get_handlers_for_event("cron.morning_briefing")) > 0


class TestDeadlineHandler:
    @pytest.mark.asyncio
    async def test_should_fire_when_task_due_soon(self, client):
        from datetime import datetime, timedelta

        from services.handlers.deadline import DeadlineHandler

        handler = DeadlineHandler()
        trigger = MagicMock()
        trigger.config = {"hours_before": 2}

        mock_task = MagicMock()
        mock_task.due_date = datetime.utcnow() + timedelta(hours=1)
        mock_task.status = "todo"

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_task)

        event = {"type": "task.created", "payload": {"task_id": "some-uuid"}, "user_id": "u1"}
        result = await handler.should_fire(event, trigger, db)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_not_fire_when_task_far(self, client):
        from datetime import datetime, timedelta

        from services.handlers.deadline import DeadlineHandler

        handler = DeadlineHandler()
        trigger = MagicMock()
        trigger.config = {"hours_before": 2}

        mock_task = MagicMock()
        mock_task.due_date = datetime.utcnow() + timedelta(hours=24)
        mock_task.status = "todo"

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_task)

        event = {"type": "task.created", "payload": {"task_id": "some-uuid"}, "user_id": "u1"}
        result = await handler.should_fire(event, trigger, db)
        assert result is False


class TestBudgetHandler:
    @pytest.mark.asyncio
    async def test_should_fire_when_over_budget(self, client):
        from services.handlers.budget import BudgetHandler

        handler = BudgetHandler()
        trigger = MagicMock()
        trigger.config = {"daily_limit": 500_000}
        trigger.user_id = "user-uuid"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 600_000
        db.execute = AsyncMock(return_value=mock_result)

        event = {"type": "expense.created", "payload": {"amount": 100_000}, "user_id": "u1"}
        result = await handler.should_fire(event, trigger, db)
        assert result is True
