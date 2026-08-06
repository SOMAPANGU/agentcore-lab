"""Topic-driven news crew: collect sources → write a reasoned story."""

from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

load_dotenv()

#define a variable named llm and assign it to the LLM object
llm = LLM(
    model="bedrock/us.amazon.nova-2-lite-v1:0",
    region_name="us-east-2",
)

#define a variable named your_app and assign it to the BedrockAgentCoreApp object
your_app = BedrockAgentCoreApp()

#define a variable named search_tool and assign it to the SerperDevTool object
search_tool = SerperDevTool()

#define a variable named scrape_tool and assign it to the ScrapeWebsiteTool object
scrape_tool = ScrapeWebsiteTool()

#define a variable named collector_agent and assign it to the Agent object
collector_agent = Agent(
    role="Senior investigative news collector",
    goal=(
        "For the user's topic, gather rich, verified notes from many reputable "
        "web sources so a writer can build an accurate story."
    ),
    backstory=(
        "You are a careful reporter. You search widely, open real article pages, "
        "skip pages that fail to load, and never invent URLs or facts. You capture "
        "enough detail (product names, numbers, competitor mentions, dates) that "
        "someone else can explain why things happened—not just what happened."
    ),
    tools=[search_tool, scrape_tool],
    llm=llm,
    allow_delegation=False,
)

storyteller_agent = Agent(
    role="Storyteller and industry analyst",
    goal=(
        "Turn collected research into a clear, human-readable story that explains "
        "connections between facts (competition, pricing, strategy)—not a bullet dump."
    ),
    backstory=(
        "You write like a sharp magazine explainer for smart non-experts. You connect "
        "dots: if one company bumps RAM or cuts price, you look for rival moves, "
        "market pressure, or supply/demand clues in the research. You never invent "
        "sources. If a link between two facts is only a hypothesis, you say so."
    ),
    tools=[],
    llm=llm,
    allow_delegation=False,
)

collect_task = Task(
    description=(
        "User topic: {topic}\n\n"
        "HARD REQUIREMENT: Include at least 5 sources whose publication/update "
        "date is within the last 60 days. Put the date on every source. If you "
        "cannot find 5 dated-within-60-days sources, keep searching with sharper "
        "queries (add year, month, quarter, 'deal', 'announces') until you can, "
        "or clearly list how many you found and why you fell short.\n\n"
        "1. Search for recent, reputable coverage (news sites, company newsrooms, "
        "reputable business/tech press). Prioritize last-60-day articles over "
        "old background (do not use old deals as primary sources).\n"
        "2. Open/scrape multiple promising pages (aim for roughly 8–15 successful "
        "reads; if scrape fails with JS/cookie walls, pick other URLs). "
        "Do not scrape the same URL twice.\n"
        "3. Prefer specific article URLs over homepages or topic hubs.\n"
        "4. Produce structured research notes only—no final story yet.\n\n"
        "For each useful source include:\n"
        "- title\n"
        "- url\n"
        "- date (required; use page date or byline date)\n"
        "- within_last_60_days: yes/no\n"
        "- 3–6 factual bullets from the page (products, numbers, quotes, "
        "competitor mentions, deals/stakes)\n"
        "- optional: 'related signals' (pricing, rivals, supply, regulation)\n\n"
        "Do not invent links, dates, or facts. Mark failed scrapes and replace them."
    ),
    expected_output=(
        "A research brief on {topic} with title, url, date, within_last_60_days, "
        "and factual bullets per source. At least 5 sources must be dated within "
        "the last 60 days. No invented URLs. No story prose yet."
    ),
    agent=collector_agent,
)

story_task = Task(
    description=(
        "User topic: {topic}\n\n"
        "Using ONLY the collector's research notes:\n"
        "1. Write a short, easy-to-read story (about 4–8 short paragraphs) that "
        "a non-expert can follow.\n"
        "2. Cover what is happening and—more importantly—why it might be "
        "happening. Connect facts across sources when the notes support it "
        "(e.g. competitor changed specs/price → pressure to match).\n"
        "3. If a causal link is inferred rather than explicitly stated in sources, "
        "label it as a possible explanation, not a proven fact.\n"
        "4. End with a 'Sources' section listing the real urls you used "
        "(titles + links from the notes only).\n"
        "5. Do not search the web. Do not invent URLs or numbers."
    ),
    expected_output=(
        "A human-readable story on {topic} with clear narrative flow, explicit "
        "cross-source reasoning where supported, honest uncertainty when guessing "
        "motive, and a Sources list of real URLs from the research notes."
    ),
    agent=storyteller_agent,
    context=[collect_task],
)

crew = Crew(
    agents=[collector_agent, storyteller_agent],
    tasks=[collect_task, story_task],
    process=Process.sequential,
)

@your_app.entrypoint
#Name of the function can be anything from here we are just choosing it as invoke but when you are doing a post call to the server agent code provides us with a slash invocations endpoint where it's going to start this endpoint and this function so the invoke is just what I chose but you can go with any name for this function doesn't matter because this is just a handler
def invoke(payload):
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise ValueError("Prompt is required")
    result = crew.kickoff(inputs={"topic": prompt})
    return {"result": result.raw}


if __name__ == "__main__":
    your_app.run()
