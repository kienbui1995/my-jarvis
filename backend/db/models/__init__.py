"""Re-export all models for backward compatibility: `from db.models import User, Task, ...`"""
from db.models.base import Base
from db.models.user import User
from db.models.conversation import Conversation, Message
from db.models.productivity import Task, CalendarEvent, Expense
from db.models.memory import Memory, KnowledgeEntity, KnowledgeRelation
from db.models.system import LLMUsage, ProactiveTrigger, Notification, MCPServer
from db.models.evidence import EvidenceLog
from db.models.preference import UserPreference, UserPromptRule, UserToolPermission

__all__ = [
    "Base", "User", "Conversation", "Message", "Task", "CalendarEvent", "Expense",
    "Memory", "KnowledgeEntity", "KnowledgeRelation",
    "LLMUsage", "ProactiveTrigger", "Notification", "MCPServer",
    "EvidenceLog", "UserPreference", "UserPromptRule", "UserToolPermission",
]
