# agentcore-lab

Build and deploy a **production-grade AI Highlights Agent** using the
[Strands Agents SDK](https://github.com/strands-agents/sdk-python) and
[AWS AgentCore](https://aws.amazon.com/bedrock/agentcore/).

## What does the agent do?

When invoked, the agent:

1. **Fetches** the latest AI news from the **top five credible sources**:
   - [MIT Technology Review](https://www.technologyreview.com/)
   - [The Verge – AI](https://www.theverge.com/ai-artificial-intelligence)
   - [Wired – AI](https://www.wired.com/tag/artificial-intelligence/)
   - [Ars Technica](https://arstechnica.com/)
   - [VentureBeat AI](https://venturebeat.com/ai/)
2. **Synthesises** the most important developments.
3. **Returns five clear highlights** written in plain English — no jargon, just the big ideas and why they matter to everyday people.

---

## Project layout

```
.
├── agent.py          # Strands agent definition
├── tools.py          # RSS-based news-fetching tool
├── server.py         # AgentCore-compatible HTTP server (port 8080)
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container image for AWS AgentCore
└── README.md
```

---

## Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.12+ |
| AWS account | With Amazon Bedrock access |
| Bedrock model | `anthropic.claude-3-5-sonnet-20241022-v2:0` (default) enabled in your region |
| AWS credentials | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (or an IAM role) |

---

## Quick start — run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set AWS credentials (or use an IAM role / ~/.aws/credentials)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# 4. Run the agent interactively
python agent.py

# 5. Or start the HTTP server
python server.py
# Then in another terminal:
curl -s -X POST http://localhost:8080/invocations \
     -H 'Content-Type: application/json' \
     -d '{"prompt": "Give me the latest AI highlights"}' | python -m json.tool
```

---

## Docker — build & run

```bash
docker build -t ai-highlights-agent .

docker run -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_REGION=us-east-1 \
  ai-highlights-agent
```

Health check:
```bash
curl http://localhost:8080/health
```

---

## Deploy to AWS AgentCore

```bash
# 1. Push the image to Amazon ECR
aws ecr create-repository --repository-name ai-highlights-agent
IMAGE_URI=$(aws ecr describe-repositories \
  --repository-names ai-highlights-agent \
  --query 'repositories[0].repositoryUri' --output text)

aws ecr get-login-password | docker login --username AWS --password-stdin $IMAGE_URI
docker tag ai-highlights-agent:latest $IMAGE_URI:latest
docker push $IMAGE_URI:latest

# 2. Create the AgentCore agent (adjust --role-arn to your execution role)
aws bedrock-agentcore create-agent-runtime \
  --agent-runtime-name ai-highlights-agent \
  --container-configuration imageUri=$IMAGE_URI:latest \
  --network-configuration networkMode=PUBLIC \
  --role-arn arn:aws:iam::<account_id>:role/AgentCoreExecutionRole

# 3. Invoke the deployed agent
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-name ai-highlights-agent \
  --content-type application/json \
  --body '{"prompt":"What are the latest AI highlights?"}'
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model ID |
| `PORT` | `8080` | Server port |

---

## HTTP API

### `GET /health`
Returns `{"status": "healthy"}` — used by AgentCore for container health checks.

### `POST /invocations`
Invoke the agent.

**Request body (JSON):**
```json
{ "prompt": "What are the latest AI highlights?" }
```

**Response body (JSON):**
```json
{ "response": "Here are today's five AI highlights…" }
```
