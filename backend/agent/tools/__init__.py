"""Tool registry — all tools available to the agent."""
from agent.tools.calendar_tools import calendar_create, calendar_list
from agent.tools.finance_tools import budget_check, expense_log
from agent.tools.google_tools import gmail_read, gmail_send, google_calendar_list
from agent.tools.graph_tools import graph_search
from agent.tools.memory_tools import memory_save, memory_search
from agent.tools.news_tools import news_vn
from agent.tools.task_tools import task_create, task_list, task_update
from agent.tools.vision_tools import analyze_file, ocr_file
from agent.tools.weather_tools import weather_vn
from agent.tools.web_tools import summarize_url, web_search

all_tools = [
    task_create, task_list, task_update,
    calendar_create, calendar_list,
    memory_save, memory_search,
    web_search, summarize_url,
    expense_log, budget_check,
    graph_search,
    # M15: Vietnamese Service Integrations
    weather_vn,
    news_vn,
    google_calendar_list, gmail_read, gmail_send,
    # M17: Vision
    analyze_file, ocr_file,
]
