"""
AI news fetching tools for the AgentCore agent.

Fetches the latest AI news from the top five credible sources using RSS feeds
and returns structured content ready for the agent to summarise.
"""

import re
from typing import Any

import feedparser
from strands import tool

# ---------------------------------------------------------------------------
# Top five credible AI news sources (RSS feeds)
# ---------------------------------------------------------------------------
TOP_AI_SOURCES: list[dict[str, Any]] = [
    {
        "name": "MIT Technology Review",
        "rss_url": "https://www.technologyreview.com/feed/",
        "keyword_filter": "artificial intelligence",
    },
    {
        "name": "The Verge – AI",
        "rss_url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "keyword_filter": None,  # feed is already AI-only
    },
    {
        "name": "Wired – AI",
        "rss_url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "keyword_filter": None,
    },
    {
        "name": "Ars Technica",
        "rss_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "keyword_filter": "ai",
    },
    {
        "name": "VentureBeat AI",
        "rss_url": "https://venturebeat.com/category/ai/feed/",
        "keyword_filter": None,
    },
]

_ARTICLES_PER_SOURCE = 3
_SUMMARY_CHAR_LIMIT = 400
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse extra whitespace."""
    return " ".join(_TAG_RE.sub(" ", text).split())


def _matches_keyword(text: str, keyword: str | None) -> bool:
    """Return True when no keyword filter is set, or the keyword appears in text."""
    if keyword is None:
        return True
    return keyword.lower() in text.lower()


@tool
def fetch_latest_ai_news() -> str:
    """Fetch the latest AI news headlines and summaries from the top five credible sources.

    Queries five well-known, credible AI news sources via their RSS feeds and
    returns up to three recent articles per source, including the title, a short
    summary, and the original URL.

    Returns:
        A formatted string containing the article titles and summaries grouped
        by source. Returns an error message for any source that cannot be
        reached so the agent can still proceed with the remaining sources.
    """
    sections: list[str] = []

    for source in TOP_AI_SOURCES:
        try:
            feed = feedparser.parse(source["rss_url"])

            # feedparser sets bozo=True when the feed could not be fetched or
            # parsed. Distinguish between a network error (no entries at all)
            # and a recoverable parse warning (entries may still be present).
            if feed.bozo and not feed.entries:
                exc_msg = str(getattr(feed, "bozo_exception", "unknown error"))
                sections.append(
                    f"### {source['name']}\n  (Feed unavailable: {exc_msg})"
                )
                continue

            items: list[str] = []

            for entry in feed.entries:
                if len(items) >= _ARTICLES_PER_SOURCE:
                    break

                title: str = entry.get("title", "").strip()
                raw_summary: str = entry.get("summary", entry.get("description", ""))
                summary: str = _strip_html(raw_summary)[:_SUMMARY_CHAR_LIMIT]
                link: str = entry.get("link", "")
                published: str = entry.get("published", "")

                combined = f"{title} {summary}"
                if not _matches_keyword(combined, source["keyword_filter"]):
                    continue

                date_str = f"  Published: {published}\n" if published else ""
                items.append(
                    f"  • {title}\n"
                    f"{date_str}"
                    f"    {summary}\n"
                    f"    Source: {link}"
                )

            if items:
                sections.append(f"### {source['name']}\n" + "\n\n".join(items))
            else:
                sections.append(
                    f"### {source['name']}\n  (No matching articles found in the latest feed)"
                )

        except Exception as exc:  # noqa: BLE001
            sections.append(f"### {source['name']}\n  (Could not retrieve feed: {exc})")

    if not sections:
        return "No AI news could be retrieved at this time."

    header = "## Latest AI News from Top Credible Sources\n\n"
    return header + "\n\n".join(sections)
