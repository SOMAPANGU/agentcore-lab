"""CrewAI tool: look up ticket status via Lambda (boto3 invoke)."""

import json
import os

import boto3
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TicketStatusInput(BaseModel):
    ticket_id: str = Field(..., description="Ticket id like INC-123")


class TicketStatusTool(BaseTool):
    name: str = "ticket_status_lookup"
    description: str = (
        "Look up an ops ticket by id (e.g. INC-123, INC-456, INC-999). "
        "Use only when the user asks about a ticket status, owner, severity, or summary."
    )
    args_schema: type[BaseModel] = TicketStatusInput

    def _run(self, ticket_id: str) -> str:
        function_name = os.environ["TICKET_STATUS_LAMBDA_NAME"]
        region = os.environ.get("AWS_REGION", "us-east-2")

        client = boto3.client("lambda", region_name=region)
        response = client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"ticket_id": ticket_id}).encode("utf-8"),
        )

        raw = response["Payload"].read().decode("utf-8")

        # Surface Lambda service errors clearly to the agent.
        if response.get("FunctionError"):
            return json.dumps(
                {
                    "error": "lambda_invoke_failed",
                    "function_error": response["FunctionError"],
                    "payload": raw,
                }
            )

        # Prefer the Lambda's JSON body when present (API Gateway-style response).
        try:
            outer = json.loads(raw)
            body = outer.get("body", raw)
            if isinstance(body, str):
                return body
            return json.dumps(body)
        except json.JSONDecodeError:
            return raw
