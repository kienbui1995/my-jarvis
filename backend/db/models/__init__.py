"""Re-export all models for backward compatibility: `from db.models import User, Task, ...`"""
from db.models.base import Base
from db.models.conversation import Conversation, Message
from db.models.evidence import EvidenceLog
from db.models.memory import KnowledgeEntity, KnowledgeRelation, Memory
from db.models.autonomy import Decision, Goal
from db.models.health import BookNote, Flashcard, HealthLog, Medication
from db.models.life import BillReminder, Contact, Document, ShoppingItem, ShoppingList, Subscription
from db.models.life import BillReminder, Contact, Document, ShoppingItem, ShoppingList, Subscription
from db.models.preference import UserPreference, UserPromptRule, UserToolPermission
from db.models.productivity import CalendarEvent, Expense, Task
from db.models.skill import Skill, SkillExecution
from db.models.system import (
    APIKey,
    CustomTool,
    GoogleOAuthToken,
    Habit,
    HabitLog,
    LLMUsage,
    MCPServer,
    Notification,
    ProactiveTrigger,
)
from db.models.user import User

__all__ = [
    "Base", "User", "Conversation", "Message", "Task", "CalendarEvent", "Expense",
    "Memory", "KnowledgeEntity", "KnowledgeRelation",
    "Skill", "SkillExecution",
    "BillReminder", "Subscription", "Contact", "Document", "ShoppingList", "ShoppingItem",
    "HealthLog", "Medication", "Flashcard", "BookNote",
    "Goal", "Decision",
    "LLMUsage", "ProactiveTrigger", "Notification", "MCPServer",
    "GoogleOAuthToken", "APIKey", "CustomTool", "Habit", "HabitLog",
    "EvidenceLog", "UserPreference", "UserPromptRule", "UserToolPermission",
]
