"""
Unit tests for the AI Highlights agent tools.

Run with:  python -m pytest test_tools.py -v
"""

import textwrap
from unittest.mock import MagicMock, patch

import pytest

from tools import (
    TOP_AI_SOURCES,
    _ARTICLES_PER_SOURCE,
    _matches_keyword,
    _strip_html,
    fetch_latest_ai_news,
)


# ---------------------------------------------------------------------------
# _strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_removes_tags(self):
        assert _strip_html("<b>Hello</b> world") == "Hello world"

    def test_collapses_whitespace(self):
        assert _strip_html("foo   <br/>   bar") == "foo bar"

    def test_plain_text_unchanged(self):
        assert _strip_html("No tags here") == "No tags here"

    def test_empty_string(self):
        assert _strip_html("") == ""

    def test_nested_tags(self):
        result = _strip_html('<div><p class="x">Text</p></div>')
        assert result == "Text"


# ---------------------------------------------------------------------------
# _matches_keyword
# ---------------------------------------------------------------------------


class TestMatchesKeyword:
    def test_no_filter_always_matches(self):
        assert _matches_keyword("anything", None) is True

    def test_keyword_found(self):
        assert _matches_keyword("OpenAI launches new AI model", "ai") is True

    def test_keyword_not_found(self):
        assert _matches_keyword("Stock market news", "artificial intelligence") is False

    def test_case_insensitive(self):
        assert _matches_keyword("Deep Learning breakthrough", "deep learning") is True


# ---------------------------------------------------------------------------
# TOP_AI_SOURCES
# ---------------------------------------------------------------------------


class TestTopAiSources:
    def test_exactly_five_sources(self):
        assert len(TOP_AI_SOURCES) == 5

    def test_all_sources_have_required_keys(self):
        for source in TOP_AI_SOURCES:
            assert "name" in source
            assert "rss_url" in source
            assert "keyword_filter" in source

    def test_rss_urls_are_strings(self):
        for source in TOP_AI_SOURCES:
            assert isinstance(source["rss_url"], str)
            assert source["rss_url"].startswith("http")


# ---------------------------------------------------------------------------
# fetch_latest_ai_news (mocked feedparser)
# ---------------------------------------------------------------------------


def _make_entry(title: str, summary: str, link: str = "https://example.com", published: str = "") -> dict:
    return {"title": title, "summary": summary, "link": link, "published": published}


def _make_feed(entries: list, bozo: bool = False) -> MagicMock:
    feed = MagicMock()
    feed.bozo = bozo
    feed.entries = entries
    feed.bozo_exception = None
    return feed


class TestFetchLatestAiNews:
    @patch("tools.feedparser.parse")
    def test_returns_articles_for_all_sources(self, mock_parse):
        mock_parse.return_value = _make_feed(
            [_make_entry(f"AI Story {i}", f"Summary {i}", published="Mon, 21 Jul 2025") for i in range(5)]
        )

        result = fetch_latest_ai_news()

        assert "## Latest AI News" in result
        for source in TOP_AI_SOURCES:
            assert source["name"] in result

    @patch("tools.feedparser.parse")
    def test_respects_articles_per_source_limit(self, mock_parse):
        entries = [_make_entry(f"Story {i}", f"Summary {i}") for i in range(10)]
        mock_parse.return_value = _make_feed(entries)

        result = fetch_latest_ai_news()

        # Each source should appear at most _ARTICLES_PER_SOURCE times
        for source in TOP_AI_SOURCES:
            source_section_start = result.find(f"### {source['name']}")
            if source_section_start == -1:
                continue
            # Find the next source section
            next_section = result.find("###", source_section_start + 1)
            section_text = result[source_section_start:next_section] if next_section != -1 else result[source_section_start:]
            bullet_count = section_text.count("  •")
            assert bullet_count <= _ARTICLES_PER_SOURCE

    @patch("tools.feedparser.parse")
    def test_handles_network_error_gracefully(self, mock_parse):
        mock_parse.return_value = _make_feed([], bozo=True)

        result = fetch_latest_ai_news()

        assert "## Latest AI News" in result
        assert "Feed unavailable" in result

    @patch("tools.feedparser.parse")
    def test_handles_exception_gracefully(self, mock_parse):
        mock_parse.side_effect = RuntimeError("Connection refused")

        result = fetch_latest_ai_news()

        assert "Could not retrieve feed" in result

    @patch("tools.feedparser.parse")
    def test_strips_html_from_summaries(self, mock_parse):
        mock_parse.return_value = _make_feed(
            [_make_entry("Title", "<p>Some <b>bold</b> text</p>")]
        )

        result = fetch_latest_ai_news()

        assert "<b>" not in result
        assert "<p>" not in result
        assert "Some bold text" in result

    @patch("tools.feedparser.parse")
    def test_keyword_filter_applied(self, mock_parse):
        # MIT Technology Review has keyword_filter="artificial intelligence"
        mit_source = next(s for s in TOP_AI_SOURCES if "MIT" in s["name"])
        keyword = mit_source["keyword_filter"]

        # First entry matches, second does not
        entries = [
            _make_entry("Artificial Intelligence breakthrough", "Great AI progress"),
            _make_entry("Sports news", "Football scores"),
        ]
        mock_parse.return_value = _make_feed(entries)

        result = fetch_latest_ai_news()

        mit_section_start = result.find(f"### {mit_source['name']}")
        mit_section_end = result.find("###", mit_section_start + 1)
        mit_section = result[mit_section_start:mit_section_end] if mit_section_end != -1 else result[mit_section_start:]

        assert "Artificial Intelligence breakthrough" in mit_section
        assert "Sports news" not in mit_section

    @patch("tools.feedparser.parse")
    def test_no_filter_sources_include_any_entry(self, mock_parse):
        # The Verge – AI has keyword_filter=None, so all entries should appear
        verge_source = next(s for s in TOP_AI_SOURCES if "Verge" in s["name"])

        entries = [_make_entry("Random topic", "Summary about anything")]
        mock_parse.return_value = _make_feed(entries)

        result = fetch_latest_ai_news()

        verge_section_start = result.find(f"### {verge_source['name']}")
        verge_section_end = result.find("###", verge_section_start + 1)
        verge_section = result[verge_section_start:verge_section_end] if verge_section_end != -1 else result[verge_section_start:]

        assert "Random topic" in verge_section
