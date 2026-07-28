# CrewAI Learning Lab — Learnings

## What I built
A single CrewAI agent that searches for recent AI news, scrapes pages, and writes 5 plain-English highlights.

## Core concepts (my words)

### Agent
- What it is: Is the main brain which uses the tools to gather information & work towards a goal
- In my project it was: News research & content simplifier agent

### Task
- What it is: A piece of work which has single goal for example gather links or fomat document. 
- Why `expected_output` matters: You are defining the output you like to see without it agent generate random outputs everytime you run the script

### Crew
- What it is: Orchestrator, which manages agent tools & eveything. A framework to create agents
- What `kickoff()` does: It starts the crew

### Tools
- What they are: Task without a tool is doing a basic work. Tools give task more power & specific information to gather
- SerperDevTool does: Get the links & little summary of what the page says
- ScrapeWebsiteTool does: Reads the contents of the page or link
- Difference between them: refer above

### Process (optional)
- What I used (sequential / single agent): Single agent

## CrewAI vs plain OpenAI
- When a simple OpenAI call is enough:
- When CrewAI (Agent/Task/Crew/Tools) is worth it:
- What I learned comparing `openai_test.py` and `ai_news_agent.py`:

## Prompt quality
- What happened when the task was vague:
- What improved when I tightened the task (e.g. retry on failed scrape):
- Goal vs Task — how they should align:

## Tool limits I hit
- Scrape failures (JavaScript / cookies):
- What the agent did when scrape failed:
- What I would change next time:

## Environment / setup lessons
- Why Python 3.12 (not 3.14):
- What a venv is (not a VM):
- uv vs pip (in one sentence):
- Why `.env` + `load_dotenv()`:

## What I’d add next
- [ ] Second agent (e.g. researcher + writer)
- [ ] Save output to `output/highlights.md`
- [ ] Better scraping (browser-based tool)
- [ ] CrewAI project scaffold (`crewai create crew`)
- [ ] Other:

## One-sentence takeaway
________________________________________________________________