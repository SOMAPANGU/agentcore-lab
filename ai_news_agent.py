from dotenv import load_dotenv
from crewai import Agent, Task, Crew
#importing search tool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

#loading the environment variables
load_dotenv()

#creating the search tool
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

#creating the explainer agent
explainer_agent = Agent(
    role="AI news explainer for non technical audience",
    goal="Turn the following AI news into exactly 5 plain-English bullet points.",
    backstory="You are an experienced news explainer with a lot of anger management issues",
    verbose=True,
    allow_delegation=False,
    #adding the search tool to the agent
    tools=[search_tool, scrape_tool]
)

#creating the task
task = Task(
    description="""Search for recent 2026 AI tech/news headlines
    Pick exactly 5 good sources (reputable, recent, not all the same site). If any of the sources is not available, pick a different reliablesource.
    Read/scrape those pages
    Write one plain-English sentence per source
    Format as the list below""",
    expected_output="Exactly 5 plain-English sentences. Example: [Title](url) — one sentence. No invented links",
    agent=explainer_agent,
    verbose=True
)

#creating the crew
crew = Crew(
    agents=[explainer_agent],
    tasks=[task],
)
result = crew.kickoff()
print(result.raw)