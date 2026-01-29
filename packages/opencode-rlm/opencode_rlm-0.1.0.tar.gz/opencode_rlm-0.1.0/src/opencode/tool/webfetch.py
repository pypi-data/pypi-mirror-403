"""
WebFetch tool for retrieving URL content.
"""

from __future__ import annotations

from typing import Any, Literal
import re

from opencode.tool.base import (
    Tool,
    ToolContext,
    ToolResult,
    make_schema,
    STRING_PARAM,
    INTEGER_PARAM,
)


class WebFetchTool(Tool):
    """Fetch content from URLs."""

    DEFAULT_TIMEOUT = 30
    MAX_CONTENT_LENGTH = 100000  # 100KB

    @property
    def name(self) -> str:
        return "webfetch"

    @property
    def description(self) -> str:
        return """Fetch content from a URL.

Retrieves content and converts to requested format (markdown by default).
HTTP URLs are automatically upgraded to HTTPS.
Results may be summarized if content is very large."""

    @property
    def parameters(self) -> dict[str, Any]:
        return make_schema(
            required=[
                ("url", "The URL to fetch content from", STRING_PARAM),
                (
                    "format",
                    "Output format: text, markdown, or html",
                    {
                        "type": "string",
                        "enum": ["text", "markdown", "html"],
                        "default": "markdown",
                    },
                ),
            ],
            optional=[
                ("timeout", "Timeout in seconds (max 120)", INTEGER_PARAM),
            ],
        )

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """Fetch URL content."""
        url = kwargs.get("url", "")
        output_format = kwargs.get("format", "markdown")
        timeout = min(kwargs.get("timeout", self.DEFAULT_TIMEOUT), 120)

        if not url:
            return ToolResult.fail("No URL provided")

        # Upgrade HTTP to HTTPS
        if url.startswith("http://"):
            url = "https://" + url[7:]

        # Validate URL
        if not url.startswith("https://"):
            return ToolResult.fail("URL must start with http:// or https://")

        try:
            import httpx
        except ImportError:
            return ToolResult.fail("httpx package required: pip install httpx")

        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=timeout
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")

                # Get content
                if (
                    "text" in content_type
                    or "html" in content_type
                    or "json" in content_type
                ):
                    content = response.text
                else:
                    return ToolResult.fail(f"Unsupported content type: {content_type}")

                # Truncate if too long
                truncated = False
                if len(content) > self.MAX_CONTENT_LENGTH:
                    content = content[: self.MAX_CONTENT_LENGTH]
                    truncated = True

                # Convert format
                if output_format == "text":
                    content = self._html_to_text(content)
                elif output_format == "markdown":
                    content = self._html_to_markdown(content)
                # else: return raw HTML

                if truncated:
                    content += "\n\n... (content truncated)"

                return ToolResult.ok(
                    content,
                    url=str(response.url),
                    status_code=response.status_code,
                    truncated=truncated,
                )

        except httpx.TimeoutException:
            return ToolResult.fail(f"Request timed out after {timeout}s")
        except httpx.HTTPError as e:
            return ToolResult.fail(f"HTTP error: {e}")
        except Exception as e:
            return ToolResult.fail(f"Request failed: {e}")

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove scripts and styles
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Replace common elements
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"<p[^>]*>", "\n\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</p>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<div[^>]*>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"<li[^>]*>", "\n- ", html, flags=re.IGNORECASE)

        # Remove all remaining tags
        html = re.sub(r"<[^>]+>", "", html)

        # Decode entities
        html = html.replace("&nbsp;", " ")
        html = html.replace("&amp;", "&")
        html = html.replace("&lt;", "<")
        html = html.replace("&gt;", ">")
        html = html.replace("&quot;", '"')

        # Clean up whitespace
        html = re.sub(r"\n\s*\n\s*\n+", "\n\n", html)
        html = html.strip()

        return html

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown (simplified)."""
        # Remove scripts and styles
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Convert headings
        for i in range(6, 0, -1):
            html = re.sub(
                rf"<h{i}[^>]*>(.*?)</h{i}>",
                r"\n" + "#" * i + r" \1\n",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # Convert links
        html = re.sub(
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            r"[\2](\1)",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Convert bold/italic
        html = re.sub(
            r"<(strong|b)[^>]*>(.*?)</\1>",
            r"**\2**",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html = re.sub(
            r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Convert code
        html = re.sub(
            r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(
            r"<pre[^>]*>(.*?)</pre>",
            r"\n```\n\1\n```\n",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Convert lists
        html = re.sub(
            r"<li[^>]*>(.*?)</li>", r"\n- \1", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(r"<[uo]l[^>]*>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</[uo]l>", "\n", html, flags=re.IGNORECASE)

        # Convert paragraphs
        html = re.sub(
            r"<p[^>]*>(.*?)</p>", r"\n\1\n", html, flags=re.DOTALL | re.IGNORECASE
        )
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)

        # Remove remaining tags
        html = re.sub(r"<[^>]+>", "", html)

        # Decode entities
        html = html.replace("&nbsp;", " ")
        html = html.replace("&amp;", "&")
        html = html.replace("&lt;", "<")
        html = html.replace("&gt;", ">")
        html = html.replace("&quot;", '"')

        # Clean up whitespace
        html = re.sub(r"\n\s*\n\s*\n+", "\n\n", html)
        html = html.strip()

        return html
