"""
Web search tool for searching the web.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from pinkyclawd.tool.base import (
    ARRAY_PARAM,
    INTEGER_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


class WebSearchTool(Tool):
    """Search the web using Exa API."""

    DEFAULT_NUM_RESULTS = 10
    MAX_RESULTS = 25

    @property
    def name(self) -> str:
        return "websearch"

    @property
    def description(self) -> str:
        return """Search the web and return relevant results.

Returns search results with titles, URLs, and snippets.
Use this for:
- Finding up-to-date information
- Researching APIs and documentation
- Answering questions about current events

Results include relevant excerpts to help find the information you need."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("query", "The search query", STRING_PARAM),
            ],
            optional=[
                (
                    "numResults",
                    f"Number of results to return (default: {self.DEFAULT_NUM_RESULTS}, max: {self.MAX_RESULTS})",
                    INTEGER_PARAM,
                ),
                (
                    "allowedDomains",
                    "Only include results from these domains",
                    ARRAY_PARAM(STRING_PARAM),
                ),
                (
                    "blockedDomains",
                    "Exclude results from these domains",
                    ARRAY_PARAM(STRING_PARAM),
                ),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute a web search."""
        query = kwargs.get("query", "")
        num_results = kwargs.get("numResults", self.DEFAULT_NUM_RESULTS)
        allowed_domains = kwargs.get("allowedDomains", [])
        blocked_domains = kwargs.get("blockedDomains", [])

        if not query:
            return ToolResult.fail("No query provided")

        # Clamp results
        num_results = min(max(1, num_results), self.MAX_RESULTS)

        # Get API key
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return ToolResult.fail(
                "EXA_API_KEY environment variable not set. "
                "Get an API key from https://exa.ai"
            )

        # Build request
        url = "https://api.exa.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "query": query,
            "numResults": num_results,
            "type": "auto",
            "contents": {
                "text": {"maxCharacters": 1000},
                "highlights": True,
            },
        }

        if allowed_domains:
            payload["includeDomains"] = allowed_domains
        if blocked_domains:
            payload["excludeDomains"] = blocked_domains

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            return ToolResult.fail("Search request timed out")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return ToolResult.fail("Invalid EXA_API_KEY")
            return ToolResult.fail(f"Search request failed: {e.response.status_code}")
        except Exception as e:
            return ToolResult.fail(f"Search request failed: {e}")

        # Format results
        results = data.get("results", [])

        if not results:
            return ToolResult.ok(f"No results found for: {query}")

        output_lines = [f"Search results for: {query}\n"]

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            text = result.get("text", "")
            highlights = result.get("highlights", [])

            output_lines.append(f"## {i}. {title}")
            output_lines.append(f"URL: {url}")

            # Use highlights if available, otherwise text excerpt
            if highlights:
                excerpt = " ... ".join(highlights[:3])
            elif text:
                excerpt = text[:500] + "..." if len(text) > 500 else text
            else:
                excerpt = "No excerpt available"

            output_lines.append(f"Excerpt: {excerpt}")
            output_lines.append("")

        return ToolResult.ok(
            "\n".join(output_lines),
            result_count=len(results),
            query=query,
        )
