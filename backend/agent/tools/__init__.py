"""Tool registry — all tools available to the agent."""
from agent.tools.task_tools import task_create, task_list, task_update
from agent.tools.calendar_tools import calendar_create, calendar_list
from agent.tools.memory_tools import memory_save, memory_search
from agent.tools.web_tools import web_search, summarize_url
from agent.tools.finance_tools import expense_log, budget_check
from agent.tools.graph_tools import graph_search

all_tools = [
    task_create, task_list, task_update,
    calendar_create, calendar_list,
    memory_save, memory_search,
    web_search, summarize_url,
    expense_log, budget_check,
    graph_search,
]
