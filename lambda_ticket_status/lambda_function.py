"""Fake ticket lookup for the ops helper lab agent."""

import json


TICKETS = {
    "INC-123": {
        "ticket_id": "INC-123",
        "status": "Investigating",
        "severity": "P2",
        "owner": "sandeep",
        "summary": "Bedrock AccessDenied on AgentCore Runtime InvokeModel",
        "service": "agentcore-ops-helper",
        "updated_at": "2026-08-14T18:00:00Z",
    },
    "INC-456": {
        "ticket_id": "INC-456",
        "status": "Resolved",
        "severity": "P3",
        "owner": "ops-team",
        "summary": "ECS service failed ELB health checks after image push",
        "service": "payments-api",
        "updated_at": "2026-08-13T12:30:00Z",
    },
    "INC-999": {
        "ticket_id": "INC-999",
        "status": "Open",
        "severity": "P1",
        "owner": "oncall",
        "summary": "EKS pods CrashLoopBackOff after bad config rollout",
        "service": "checkout",
        "updated_at": "2026-08-14T21:00:00Z",
    },
}


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """
    Accepts either:
      {"ticket_id": "INC-123"}
    or API Gateway style:
      {"body": "{\"ticket_id\": \"INC-123\"}"}
    """
    payload = event or {}

    if isinstance(payload.get("body"), str):
        try:
            payload = json.loads(payload["body"] or "{}")
        except json.JSONDecodeError:
            return _response(400, {"error": "body must be valid JSON"})

    ticket_id = (
        payload.get("ticket_id")
        or payload.get("ticketId")
        or payload.get("id")
        or ""
    )
    ticket_id = str(ticket_id).strip().upper()

    if not ticket_id:
        return _response(
            400,
            {
                "error": "ticket_id is required",
                "example": {"ticket_id": "INC-123"},
                "known_tickets": sorted(TICKETS.keys()),
            },
        )

    ticket = TICKETS.get(ticket_id)
    if not ticket:
        return _response(
            404,
            {
                "error": "ticket not found",
                "ticket_id": ticket_id,
                "known_tickets": sorted(TICKETS.keys()),
            },
        )

    return _response(200, ticket)
