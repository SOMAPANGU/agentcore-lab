import os

from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools.aws.bedrock.knowledge_base.retriever_tool import BedrockKBRetrieverTool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from ticket_status_tool import TicketStatusTool

load_dotenv()

#define a variable named llm and assign it to the LLM object
llm = LLM(
    model="bedrock/us.amazon.nova-2-lite-v1:0",
    region_name="us-east-2",
)

kb_tool = BedrockKBRetrieverTool(
    knowledge_base_id=os.environ["BEDROCK_KNOWLEDGE_BASE_ID"],
    number_of_results=5
)

#define a variable named your_app and assign it to the BedrockAgentCoreApp object
ops_helper_app = BedrockAgentCoreApp()

#define a variable named ops_helper_agent and assign it to the Agent object
ops_helper_agent = Agent(
    role="Senior Ops Assistant",
    goal=(
        "Help users understand and answer questions about the company's operations accurately."
    ), 
    backstory=(       
        "You are an experienced operations specialist who understands the company's systems, processes, and day-to-day operations. You are careful with facts and never guess when information is missing."
    ),
    llm=llm,
    allow_delegation=False,
    tools=[kb_tool, TicketStatusTool()],
)

ops_helper_task = Task(
    description=(
        "User question: {question}\n\n"
        "Gather the information needed to answer the question, then summarize "
        "it into a clear final answer.\n\n"
        "- For runbooks / how-to / ops process questions: use the knowledge base.\n"
        "- For ticket questions (id, status, owner, severity, summary): use "
        "ticket_status_lookup.\n"
        "- If both are needed: use both, then combine into one answer.\n\n"
        "Do not make up any information. If information is missing, say so."
    ),
    expected_output=(
        "A clear, concise final answer:\n"
        "1. Brief summary of the answer.\n"
        "2. Say so if information is unavailable.\n"
        "3. Include the source (knowledge base and/or ticket lookup)."
    ),
    agent=ops_helper_agent,
)

crew = Crew(
    agents=[ops_helper_agent],
    tasks=[ops_helper_task],
)

@ops_helper_app.entrypoint
#Name of the function can be anything from here we are just choosing it as invoke but when you are doing a post call to the server agent code provides us with a slash invocations endpoint where it's going to start this endpoint and this function so the invoke is just what I chose but you can go with any name for this function doesn't matter because this is just a handler
def invoke(payload):
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise ValueError("Prompt is required")
    result = crew.kickoff(inputs={"question": prompt})
    return {"result": result.raw}


if __name__ == "__main__":
    ops_helper_app.run()
