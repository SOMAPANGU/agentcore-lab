# Lambda ops runbook

## What Lambda is (ops view)
AWS Lambda runs short-lived functions. No servers to patch. Failures show up as errors, timeouts, or throttling in CloudWatch Metrics/Logs.

## Invoke failures checklist
1. Confirm the function exists in the expected region.
2. Check the latest CloudWatch Log stream for the stack trace.
3. Timeout too low? Increase timeout or reduce work per invoke.
4. Memory too low? Increase memory (also increases CPU allocation).
5. Permissions: does the execution role allow the AWS calls the code makes (S3, Bedrock, DynamoDB, etc.)?
6. VPC Lambdas: confirm ENIs/subnets/NAT if the function must reach the internet.

## Ticket tool pattern (ops helper lab)
Our ops helper may call a Lambda like `get_ticket_status`:
- Input: `{ "ticket_id": "INC-123" }`
- Output: JSON with status, owner, severity, summary
- If the ticket ID is unknown, return a clear "not found" — do not invent tickets.

## Versioning
- Use published versions + aliases (`live`, `lab`) for safer rollouts.
- Point the agent/tool at an alias, not `$LATEST`, when you need stable behavior.

## Cold starts
First invoke after idle can be slower. For a lab this is normal. For latency-sensitive paths, consider provisioned concurrency only if needed.
