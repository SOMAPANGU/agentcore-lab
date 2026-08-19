# AgentCore / Bedrock ops notes (lab)

## Runtime deploy loop
1. Build ARM64 image.
2. Tag to ECR (use a dedicated tag per agent, e.g. `ops-helper`, not one shared `:latest` for every app).
3. Push to ECR.
4. Update AgentCore Runtime to pick up the new image digest.
5. Invoke and verify in CloudWatch / Observability.

## Common Bedrock errors
### AccessDenied on InvokeModel
- Execution role missing `bedrock:InvokeModel` / stream permissions.
- Model not available / not enabled in the region.
- Wrong region in code vs Runtime.

### Input is too long for requested model
- Tool/scrape returned huge content (e.g. raw PDF).
- Prefer HTML docs and short runbooks; skip giant binaries.

## Knowledge Base
- Store curated runbooks in S3.
- Use a **vector** Knowledge Base (not Redshift structured KB).
- After uploading new `.md` files, **sync/ingest** the data source.
- Do not dump CloudWatch logs into the Knowledge Base.

## Secrets
- Do not bake API keys into images.
- Pass secrets as Runtime environment variables or Secrets Manager references.
