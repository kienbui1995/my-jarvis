"""Custom Tools SDK — user-defined tools with sandboxed execution."""
import ast
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.system import CustomTool

logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT = 30  # seconds
BLOCKED_IMPORTS = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "ctypes"}


def validate_tool_code(code: str) -> str | None:
    """Validate tool code is safe. Returns error message or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"

    # Check for dangerous imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BLOCKED_IMPORTS:
                    return f"Import not allowed: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in BLOCKED_IMPORTS:
                return f"Import not allowed: {node.module}"

    # Must have exactly one function
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if len(funcs) != 1:
        return "Code must contain exactly one function"

    return None


def extract_tool_metadata(code: str) -> dict:
    """Extract function name, docstring, and args from code."""
    tree = ast.parse(code)
    func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    docstring = ast.get_docstring(func) or ""
    args = [
        arg.arg for arg in func.args.args
        if arg.arg not in ("self", "cls")
    ]
    return {"name": func.name, "description": docstring, "args": args}


async def execute_custom_tool(
    code: str, args: dict, timeout: int = EXECUTION_TIMEOUT,
) -> str:
    """Execute custom tool code in restricted scope."""
    import asyncio

    namespace = {"__builtins__": {
        "str": str, "int": int, "float": float, "bool": bool,
        "list": list, "dict": dict, "len": len, "range": range,
        "print": lambda *a: None,  # no-op print
        "isinstance": isinstance, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter,
        "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
        "sorted": sorted, "reversed": reversed,
        "__import__": __import__,  # needed for allowed imports
    }}

    try:
        exec(code, namespace)
        # Find the function
        func = next(
            v for k, v in namespace.items()
            if callable(v) and k != "__builtins__" and not k.startswith("_")
        )
        result = await asyncio.wait_for(
            asyncio.to_thread(func, **args),
            timeout=timeout,
        )
        return str(result)
    except asyncio.TimeoutError:
        return f"Tool timed out ({timeout}s)"
    except Exception as e:
        return f"Tool error: {e}"


async def list_user_tools(user_id: str, db: AsyncSession) -> list[dict]:
    """List custom tools for a user."""
    rows = (await db.execute(
        select(CustomTool).where(CustomTool.user_id == UUID(user_id))
    )).scalars().all()
    return [
        {"id": str(t.id), "name": t.name, "description": t.description, "enabled": t.enabled}
        for t in rows
    ]
