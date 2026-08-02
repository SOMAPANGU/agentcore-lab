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
collector_agent = Agent(
    role="Your role is a senior news journalist",
    goal="Gather all the top news headlines that happened around the world",
    backstory="You are an experienced news journalist with attention to detail on the news you collect & you always verify the sources you collect the news from",
    verbose=True,
    allow_delegation=False,
    #adding the search tool to the agent
    tools=[search_tool, scrape_tool]
)

#creating the task
collector_task = Task(
    description="""Search for recent 2026 news headlines
    Always look for reputable, recent sources not all the same site. If any of the sources is not available, pick a different reliable source.
    Read/scrape those pages
    Write one plain-English sentence per source
    Format as the list below""",
    expected_output="A list of news headlines in the format of [Title](url) — one sentence. No invented links",
    agent=collector_agent,
    verbose=True
)

curator_agent = Agent(
    role="Your role is a senior news curator",
    goal="Pick the news headlines from the collector agent & sort them in order based on the importance & topic they belong to",
    backstory="You are an experienced news curator with a knack for picking the most important news headlines & you always adds your view on the news you publish",
    verbose=True,
    allow_delegation=False,
)

#creating the curator task
curator_task = Task(
    description="Read the news headlines from the collector agent & curate them based on the importance & topic they belong to & write a summary of the most important news headlines in the format of [Title](url) — one sentence. No invented links",
    expected_output="A summary of the most important news headlines in the format of [Title](url) — one sentence. No invented links",
    agent=curator_agent,
    context=[collector_task.],
    verbose=True
)

#creating the crew
crew = Crew(
    agents=[collector_agent, curator_agent],
    tasks=[collector_task, curator_task],
    verbose=True,
)
result = crew.kickoff()
print(result.raw)