"""
AI Highlights Agent — powered by Strands & deployed on AWS AgentCore.

The agent fetches the latest AI news from the top five credible sources and
presents clear, jargon-free highlights that anyone can understand.
"""

import os

from strands import Agent
from strands.models import BedrockModel

from tools import fetch_latest_ai_news

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a friendly AI news curator who makes the latest \
developments in artificial intelligence easy for everyone to understand.

When asked about recent AI news or highlights:
1. Call the `fetch_latest_ai_news` tool to retrieve the freshest articles.
2. Read all the headlines and summaries carefully.
3. Pick the most important or interesting developments across all sources.
4. Present **five clear highlights**, numbered 1–5.

For each highlight:
- Write 2–3 plain-English sentences that a non-technical person can follow.
- If you must use a technical term, briefly explain it in parentheses.
- Focus on *why it matters* to everyday people, not just what happened.
- Keep a positive, curious, and accessible tone.

Begin your response with a one-sentence intro line, then list the five highlights.
Do not include URLs or source names in the highlights themselves."""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_agent() -> Agent:
    """Create and return a configured Strands agent."""
    model = BedrockModel(
        model_id=os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
        ),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    return Agent(
        model=model,
        tools=[fetch_latest_ai_news],
        system_prompt=SYSTEM_PROMPT,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("AI Highlights Agent — fetching the latest from across the web…\n")
    agent = create_agent()
    agent("What are the five most important AI highlights right now?")
