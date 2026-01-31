"""Web tools - Search the internet and fetch pages.

These tools give Albus access to real-time information from the web.
"""

from __future__ import annotations

import logging
from typing import Any

from stdlib.registry import register_tool

logger = logging.getLogger(__name__)


# =============================================================================
# WEB SEARCH (DuckDuckGo - no API key required)
# =============================================================================


@register_tool(
    "web.search",
    description="Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 5, max: 10)",
                "default": 5,
            },
            "region": {
                "type": "string",
                "description": "Region code (e.g., 'us-en', 'uk-en'). Default: 'wt-wt' (no region)",
                "default": "wt-wt",
            },
        },
        "required": ["query"],
    },
)
async def web_search(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Search the web using DuckDuckGo.

    Returns:
        {
            "success": true,
            "query": "...",
            "results": [
                {"title": "...", "url": "...", "snippet": "..."},
                ...
            ]
        }
    """
    query = inputs.get("query", "").strip()
    if not query:
        return {"success": False, "error": "query is required", "results": []}

    max_results = min(int(inputs.get("max_results", 5)), 10)
    region = inputs.get("region", "wt-wt")

    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {
                "success": False,
                "error": "ddgs not installed. Run: pip install ddgs",
                "results": [],
            }

    try:
        results = []
        ddgs = DDGS()
        for r in ddgs.text(query, region=region, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                }
            )

        logger.debug("web.search: query=%r results=%d", query, len(results))
        return {
            "success": True,
            "query": query,
            "results": results,
        }

    except Exception as e:
        logger.warning("web.search failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": [],
        }


# =============================================================================
# WEB FETCH (Get page content)
# =============================================================================


@register_tool(
    "web.fetch",
    description="Fetch content from a URL. Returns text content (HTML stripped for readability).",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch",
            },
            "extract_text": {
                "type": "boolean",
                "description": "Extract readable text (strip HTML). Default: true",
                "default": True,
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum content length in characters. Default: 10000",
                "default": 10000,
            },
        },
        "required": ["url"],
    },
)
async def web_fetch(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Fetch content from a URL.

    Returns:
        {
            "success": true,
            "url": "...",
            "content": "...",
            "content_type": "...",
            "length": 1234
        }
    """
    url = inputs.get("url", "").strip()
    if not url:
        return {"success": False, "error": "url is required", "content": ""}

    extract_text = inputs.get("extract_text", True)
    max_length = int(inputs.get("max_length", 10000))

    try:
        import aiohttp
    except ImportError:
        return {
            "success": False,
            "error": "aiohttp not installed",
            "content": "",
        }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status}",
                        "url": url,
                        "content": "",
                    }

                content_type = resp.headers.get("Content-Type", "")
                raw_content = await resp.text()

                # Extract text if requested and it's HTML
                content = raw_content
                if extract_text and "html" in content_type.lower():
                    content = _extract_text_from_html(raw_content)

                # Truncate if too long
                if len(content) > max_length:
                    content = (
                        content[:max_length] + f"\n\n[Truncated at {max_length} chars]"
                    )

                logger.debug("web.fetch: url=%r length=%d", url, len(content))
                return {
                    "success": True,
                    "url": url,
                    "content": content,
                    "content_type": content_type,
                    "length": len(content),
                }

    except Exception as e:
        logger.warning("web.fetch failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "content": "",
        }


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML, stripping tags and scripts."""
    import re

    # Remove script and style elements
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)

    return text.strip()


# =============================================================================
# NEWS SEARCH
# =============================================================================


@register_tool(
    "web.news",
    description="Search recent news articles using DuckDuckGo News.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "News search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
)
async def web_news(inputs: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Search recent news using DuckDuckGo News.

    Returns:
        {
            "success": true,
            "query": "...",
            "results": [
                {"title": "...", "url": "...", "source": "...", "date": "...", "snippet": "..."},
                ...
            ]
        }
    """
    query = inputs.get("query", "").strip()
    if not query:
        return {"success": False, "error": "query is required", "results": []}

    max_results = min(int(inputs.get("max_results", 5)), 10)

    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {
                "success": False,
                "error": "ddgs not installed. Run: pip install ddgs",
                "results": [],
            }

    try:
        results = []
        ddgs = DDGS()
        for r in ddgs.news(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", r.get("link", "")),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "snippet": r.get("body", r.get("excerpt", "")),
                }
            )

        logger.debug("web.news: query=%r results=%d", query, len(results))
        return {
            "success": True,
            "query": query,
            "results": results,
        }

    except Exception as e:
        logger.warning("web.news failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": [],
        }


__all__ = [
    "web_search",
    "web_fetch",
    "web_news",
]
