"""Tool registry — auto-discovers all @tool decorated functions in agent/tools/.

New tools: just create a file in agent/tools/, use @tool decorator. No manual registration needed.
"""
import importlib
import logging
import pkgutil
from pathlib import Path

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def _discover_tools() -> list[BaseTool]:
    """Scan agent/tools/ modules and collect all BaseTool instances."""
    tools = []
    package_dir = Path(__file__).parent
    seen_names = set()

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"agent.tools.{module_info.name}")
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if isinstance(obj, BaseTool) and obj.name not in seen_names:
                    tools.append(obj)
                    seen_names.add(obj.name)
        except Exception:
            logger.warning(f"Failed to load tool module: agent.tools.{module_info.name}", exc_info=True)

    logger.info(f"Discovered {len(tools)} tools from {len(list(pkgutil.iter_modules([str(package_dir)])))} modules")
    return tools


all_tools = _discover_tools()
