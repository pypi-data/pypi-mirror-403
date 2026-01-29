"""
Memory tools for RLM context retrieval.
"""

from __future__ import annotations

from typing import Any

from pinkyclawd.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    INTEGER_PARAM,
)
from pinkyclawd.rlm.search import get_searcher
from pinkyclawd.rlm.retrieve import get_retriever


class MemoryTool(Tool):
    """Search and retrieve archived conversation context."""

    @property
    def name(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return """Search and retrieve context from previous conversations in this session.

Use when:
- User references something discussed earlier
- You need details about files, decisions, or code from earlier
- User asks "remember when we..." or "what did we decide about..."

The tool searches through archived conversation summaries and content."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "query",
                    "Search query to find relevant archived context",
                    STRING_PARAM,
                ),
            ],
            optional=[
                (
                    "limit",
                    "Maximum number of context blocks to retrieve (default: 3, max: 10)",
                    INTEGER_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Search archived context."""
        query = kwargs.get("query", "")
        limit = min(kwargs.get("limit", 3), 10)

        if not query:
            return ToolResult.fail("No query provided")

        # Search the RLM context store
        searcher = get_searcher()
        results = searcher.search(
            query=query,
            session_id=ctx.session_id,
            limit=limit,
        )

        if not results:
            return ToolResult.ok(
                f"No archived context found for: {query}",
                query=query,
                limit=limit,
                results=[],
            )

        # Format results for the model
        formatted_results = []
        context_text = []

        for result in results:
            block = result.block
            formatted_results.append({
                "block_id": block.id,
                "task_description": block.task_description,
                "summary": block.summary,
                "score": result.score,
                "tokens": block.tokens,
                "created_at": block.created_at.isoformat(),
            })

            # Build readable context
            context_text.append(f"--- Context Block (Score: {result.score:.2f}) ---")
            if block.task_description:
                context_text.append(f"Task: {block.task_description}")
            context_text.append(f"Summary: {block.summary}")
            context_text.append("")
            context_text.append(block.content)
            context_text.append("")

        return ToolResult.ok(
            "\n".join(context_text),
            query=query,
            limit=limit,
            results=formatted_results,
            result_count=len(results),
        )


class RLMQueryTool(Tool):
    """Execute Python queries on archived context across all sessions."""

    @property
    def name(self) -> str:
        return "rlm_query"

    @property
    def description(self) -> str:
        return """Execute Python code to query ALL archived conversation context globally.

Available functions:
- search(query: str, limit: int = 10) -> list[dict]: Search all archived context
- get_recent(n: int = 10) -> list[dict]: Get N most recent context blocks
- get_by_task(task_id: str) -> dict | None: Get context for specific task
- get_by_session(session_id: str) -> list[dict]: Get all blocks from session
- list_tasks() -> list[dict]: List all archived tasks
- list_sessions() -> list[dict]: List all sessions with archived context

Each block contains: id, session_id, task_id, task_description, summary, content, tokens, created_at"""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "code",
                    "Python code with access to RLM query functions. Results should be printed.",
                    STRING_PARAM,
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute RLM query code."""
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr

        from pinkyclawd.rlm.retrieve import (
            search,
            get_recent,
            get_by_task,
            get_by_session,
            list_tasks,
            list_sessions,
        )

        code = kwargs.get("code", "")

        if not code:
            return ToolResult.fail("No code provided")

        # Create a restricted namespace with RLM query functions
        namespace = {
            "search": search,
            "get_recent": get_recent,
            "get_by_task": get_by_task,
            "get_by_session": get_by_session,
            "list_tasks": list_tasks,
            "list_sessions": list_sessions,
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "sorted": sorted,
            "enumerate": enumerate,
            "range": range,
            "True": True,
            "False": False,
            "None": None,
        }

        # Capture stdout
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)

            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()

            if errors:
                return ToolResult.ok(
                    f"Output:\n{output}\n\nWarnings:\n{errors}",
                    code=code,
                    output=output,
                    warnings=errors,
                )

            return ToolResult.ok(
                output or "(No output)",
                code=code,
                output=output,
            )

        except SyntaxError as e:
            return ToolResult.fail(
                f"Syntax error in code: {e}",
                code=code,
            )
        except Exception as e:
            return ToolResult.fail(
                f"Execution error: {type(e).__name__}: {e}",
                code=code,
            )
