"""
Batch tool for executing multiple tools in parallel.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pinkyclawd.tool.base import (
    ARRAY_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


class BatchTool(Tool):
    """Execute multiple tools in parallel."""

    MAX_PARALLEL_TOOLS = 25

    @property
    def name(self) -> str:
        return "batch"

    @property
    def description(self) -> str:
        return """Execute multiple tool calls in parallel.

Use this to run up to 25 independent tool operations concurrently.
All tools run in parallel and results are collected.
Individual tool failures don't stop other tools from running.

Each invocation contains:
- tool: The name of the tool to execute
- arguments: The arguments for that tool"""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                (
                    "invocations",
                    "Array of tool invocations to execute in parallel",
                    ARRAY_PARAM(
                        {
                            "type": "object",
                            "properties": {
                                "tool": {
                                    "type": "string",
                                    "description": "Name of the tool to execute",
                                },
                                "arguments": {
                                    "type": "object",
                                    "description": "Arguments to pass to the tool",
                                },
                            },
                            "required": ["tool", "arguments"],
                        }
                    ),
                ),
            ],
        )

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute multiple tools in parallel."""
        invocations = kwargs.get("invocations", [])

        if not invocations:
            return ToolResult.fail("No invocations provided")

        if not isinstance(invocations, list):
            return ToolResult.fail("Invocations must be an array")

        if len(invocations) > self.MAX_PARALLEL_TOOLS:
            return ToolResult.fail(
                f"Too many invocations ({len(invocations)}). "
                f"Maximum is {self.MAX_PARALLEL_TOOLS}."
            )

        # Import here to avoid circular imports
        from pinkyclawd.tool.registry import get_tool_registry

        registry = get_tool_registry()

        async def execute_single(index: int, invocation: dict) -> dict[str, Any]:
            """Execute a single tool invocation."""
            if not isinstance(invocation, dict):
                return {
                    "index": index,
                    "success": False,
                    "error": "Invocation is not an object",
                }

            tool_name = invocation.get("tool", "")
            arguments = invocation.get("arguments", {})

            if not tool_name:
                return {
                    "index": index,
                    "success": False,
                    "error": "No tool name provided",
                }

            try:
                result = await registry.execute(tool_name, ctx, arguments)
                return {
                    "index": index,
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                }
            except Exception as e:
                return {
                    "index": index,
                    "tool": tool_name,
                    "success": False,
                    "error": str(e),
                }

        # Execute all tools in parallel
        tasks = [execute_single(i, inv) for i, inv in enumerate(invocations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        output_lines: list[str] = []
        success_count = 0
        failure_count = 0

        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
                output_lines.append(f"Error: {result}")
                continue

            index = result.get("index", "?")
            tool = result.get("tool", "unknown")
            success = result.get("success", False)

            if success:
                success_count += 1
                output_lines.append(f"[{index + 1}] {tool}: SUCCESS")
                output_text = result.get("output", "")
                if output_text:
                    # Indent output
                    indented = "\n".join(f"    {line}" for line in output_text.split("\n")[:10])
                    output_lines.append(indented)
                    if len(output_text.split("\n")) > 10:
                        output_lines.append("    ... (truncated)")
            else:
                failure_count += 1
                error = result.get("error", "Unknown error")
                output_lines.append(f"[{index + 1}] {tool}: FAILED - {error}")

        # Summary
        summary = f"\nBatch complete: {success_count} succeeded, {failure_count} failed"
        output_lines.append(summary)

        all_success = failure_count == 0
        return ToolResult(
            success=all_success,
            output="\n".join(output_lines),
            error=None if all_success else f"{failure_count} tool(s) failed",
            metadata={
                "total": len(invocations),
                "success_count": success_count,
                "failure_count": failure_count,
            },
        )
