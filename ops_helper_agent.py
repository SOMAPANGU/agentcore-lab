"""Ops helper agent: Bedrock KB + AgentCore Gateway (MCP) ticket tools.

Flow (remember this):
  1) app.run() starts the HTTP server and waits.
  2) AgentCore POSTs /invocations -> invoke(payload) runs.
  3) We get a Cognito JWT, open an MCP session to the Gateway,
     attach KB + Gateway tools to the agent, then crew.kickoff().
  4) When invoke ends, the MCP session closes.
"""

import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from crewai import Agent, Crew, Task, LLM
from crewai_tools import MCPServerAdapter
from crewai_tools.aws.bedrock.knowledge_base.retriever_tool import BedrockKBRetrieverTool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Load .env for local runs. On AgentCore Runtime, use Runtime env vars instead.
load_dotenv()

# ---------------------------------------------------------------------------
# Shared pieces created once when the container starts
# ---------------------------------------------------------------------------

# Brain: Bedrock model the agent will use for reasoning + tool choice.
llm = LLM(
    model="bedrock/us.amazon.nova-2-lite-v1:0",
    region_name="us-east-2",
)

# Local CrewAI tool (NOT via Gateway): retrieves chunks from Bedrock Knowledge Base.
kb_tool = BedrockKBRetrieverTool(
    knowledge_base_id=os.environ["BEDROCK_KNOWLEDGE_BASE_ID"],
    number_of_results=5,
)

# AgentCore Runtime app: exposes /ping and /invocations for this container.
ops_helper_app = BedrockAgentCoreApp()


def get_gateway_access_token() -> str:
    """Same idea as your curl to Cognito /oauth2/token (client_credentials).

    Gateway inbound auth is JWT. Without this token, tools/list and tools/call
    on the Gateway MCP URL will fail (401).
    """
    token_url = os.environ["COGNITO_TOKEN_URL"]
    client_id = os.environ["COGNITO_CLIENT_ID"]
    client_secret = os.environ["COGNITO_CLIENT_SECRET"]
    scope = os.environ["COGNITO_SCOPE"]

    # Form body: grant_type + scope (same as curl -d ...)
    body = urlencode(
        {
            "grant_type": "client_credentials",
            "scope": scope,
        }
    ).encode("utf-8")

    # Basic auth = client_id:client_secret (same as curl -u ...)
    import base64

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode(
        "ascii"
    )
    req = Request(
        token_url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic}",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        import json

        data = json.loads(resp.read().decode("utf-8"))

    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in Cognito response: {data}")
    return token


def build_gateway_server_params() -> dict:
    """Build the dict MCPServerAdapter needs to reach AgentCore Gateway.

    - url: Gateway MCP endpoint (.../mcp)
    - transport: streamable-http  (remote HTTPS MCP; not stdio, not SSE-only)
    - headers: Bearer JWT from Cognito
    """
    token = get_gateway_access_token()
    return {
        "url": os.environ["GATEWAY_URL"],
        "transport": "streamable-http",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/event-stream",
        },
    }


# ---------------------------------------------------------------------------
# Entrypoint: runs once per /invocations request
# ---------------------------------------------------------------------------

@ops_helper_app.entrypoint
def invoke(payload):
    # Payload key from AgentCore (you chose "prompt"). This is just a Python variable.
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise ValueError("Prompt is required")

    # Open MCP for THIS invoke so the Gateway session stays alive during kickoff.
    # MCPServerAdapter (hidden): connects, runs tools/list, returns CrewAI tools.
    # When the agent later picks a ticket tool, the adapter runs tools/call for you.
    with MCPServerAdapter(build_gateway_server_params(), connect_timeout=60) as mcp_tools:
        print(f"Gateway MCP tools: {[t.name for t in mcp_tools]}")

        # Agent = who is working (identity + tools). Does NOT hold {question} itself.
        ops_helper_agent = Agent(
            role="Senior Ops Assistant",
            goal=(
                "Help users understand and answer questions about the company's "
                "operations accurately."
            ),
            backstory=(
                "You are an experienced operations specialist who understands the "
                "company's systems, processes, and day-to-day operations. You are "
                "careful with facts and never guess when information is missing."
            ),
            llm=llm,
            allow_delegation=False,
            # *mcp_tools unpacks the list into individual tools.
            # Example: [kb_tool, *mcp_tools] -> [kb_tool, ops_lambda___ticket_status_lookup]
            tools=[kb_tool, *mcp_tools],
        )

        # Task = this run's work order. {question} is a CrewAI placeholder.
        # It gets filled by kickoff(inputs={"question": ...}) below.
        ops_helper_task = Task(
            description=(
                "User question: {question}\n\n"
                "Gather the information needed to answer the question, then summarize "
                "it into a clear final answer.\n\n"
                "- For runbooks / how-to / ops process questions: use the knowledge base.\n"
                "- For ticket questions (id, status, owner, severity, summary): use the "
                "ticket status lookup tool from the gateway "
                "(name may look like ops_lambda___ticket_status_lookup).\n"
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

        # Crew = wires agent + task. Building it does NOT run anything yet.
        crew = Crew(
            agents=[ops_helper_agent],
            tasks=[ops_helper_task],
        )

        # kickoff = actually run the crew.
        # inputs key "question" MUST match the task placeholder {question}.
        # Value is the user text from payload["prompt"].
        # Without this line, the LLM/tools never run.
        result = crew.kickoff(inputs={"question": prompt})
        return {"result": result.raw}


# Container start: start the HTTP server and WAIT for /invocations.
# This does not answer questions by itself — invoke() does that per request.
if __name__ == "__main__":
    ops_helper_app.run()
