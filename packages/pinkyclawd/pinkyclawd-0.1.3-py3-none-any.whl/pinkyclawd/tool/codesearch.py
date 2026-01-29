"""
Code search tool for searching code-specific content and documentation.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from pinkyclawd.tool.base import (
    INTEGER_PARAM,
    STRING_PARAM,
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
)


class CodeSearchTool(Tool):
    """Search for code, APIs, and documentation using Exa API."""

    DEFAULT_NUM_RESULTS = 10
    MAX_RESULTS = 25

    # Default domains for code/documentation search
    CODE_DOMAINS = [
        "github.com",
        "stackoverflow.com",
        "docs.python.org",
        "developer.mozilla.org",
        "docs.rs",
        "pkg.go.dev",
        "typescriptlang.org",
        "reactjs.org",
        "vuejs.org",
        "angular.io",
        "npmjs.com",
        "pypi.org",
        "crates.io",
        "rubygems.org",
        "maven.apache.org",
        "docs.microsoft.com",
        "learn.microsoft.com",
        "cloud.google.com",
        "docs.aws.amazon.com",
        "en.cppreference.com",
        "cplusplus.com",
        "rust-lang.org",
        "kotlinlang.org",
        "dart.dev",
        "swift.org",
        "docs.oracle.com",
    ]

    @property
    def name(self) -> str:
        return "codesearch"

    @property
    def description(self) -> str:
        return """Search for code, APIs, and technical documentation.

Optimized for finding:
- Code examples and implementations
- API documentation
- Library/framework documentation
- Stack Overflow answers
- GitHub repositories

Results are filtered to programming-related domains."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("query", "The search query (code, API, or documentation)", STRING_PARAM),
            ],
            optional=[
                (
                    "numResults",
                    f"Number of results (default: {self.DEFAULT_NUM_RESULTS}, max: {self.MAX_RESULTS})",
                    INTEGER_PARAM,
                ),
                (
                    "language",
                    "Programming language to focus on (e.g., 'python', 'javascript')",
                    STRING_PARAM,
                ),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Execute a code search."""
        query = kwargs.get("query", "")
        num_results = kwargs.get("numResults", self.DEFAULT_NUM_RESULTS)
        language = kwargs.get("language", "")

        if not query:
            return ToolResult.fail("No query provided")

        # Clamp results
        num_results = min(max(1, num_results), self.MAX_RESULTS)

        # Enhance query with language if provided
        if language:
            query = f"{language} {query}"

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
            "includeDomains": self.CODE_DOMAINS,
            "contents": {
                "text": {"maxCharacters": 2000},
                "highlights": True,
            },
        }

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
            return ToolResult.ok(f"No code results found for: {query}")

        output_lines = [f"Code search results for: {query}\n"]

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            result_url = result.get("url", "")
            text = result.get("text", "")
            highlights = result.get("highlights", [])

            # Determine source type
            source_type = "📄"
            if "github.com" in result_url:
                source_type = "🔗 GitHub"
            elif "stackoverflow.com" in result_url:
                source_type = "❓ StackOverflow"
            elif "docs." in result_url or "doc." in result_url:
                source_type = "📚 Docs"

            output_lines.append(f"## {i}. [{source_type}] {title}")
            output_lines.append(f"URL: {result_url}")

            # Use highlights if available, otherwise text excerpt
            if highlights:
                # For code, show more highlights
                excerpt = "\n".join(f"  - {h}" for h in highlights[:5])
            elif text:
                excerpt = text[:800] + "..." if len(text) > 800 else text
            else:
                excerpt = "No excerpt available"

            output_lines.append(f"Content:\n{excerpt}")
            output_lines.append("")

        return ToolResult.ok(
            "\n".join(output_lines),
            result_count=len(results),
            query=query,
            language=language if language else None,
        )
