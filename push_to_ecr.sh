#!/usr/bin/env bash
# Build an ARM64 image and push it to this lab's ECR repo.
#
# Usage:
#   ./push_to_ecr.sh <ecr-tag> [dockerfile]
#
# Examples:
#   ./push_to_ecr.sh ops-helper
#   ./push_to_ecr.sh ops-helper Dockerfile-ops
#   ./push_to_ecr.sh latest Dockerfile
#
# Env overrides (optional):
#   AWS_PROFILE   default: sandeep
#   AWS_REGION    default: us-east-2
#   ECR_REGISTRY  default: 321573752629.dkr.ecr.us-east-2.amazonaws.com
#   ECR_REPO      default: agentcore

set -euo pipefail

TAG="${1:-}"
DOCKERFILE="${2:-}"

if [[ -z "${TAG}" ]]; then
  echo "Usage: $0 <ecr-tag> [dockerfile]"
  echo "Example: $0 ops-helper Dockerfile-ops"
  exit 1
fi

# Sensible defaults for this lab
if [[ -z "${DOCKERFILE}" ]]; then
  if [[ "${TAG}" == "ops-helper" ]]; then
    DOCKERFILE="Dockerfile-ops"
  else
    DOCKERFILE="Dockerfile"
  fi
fi

AWS_PROFILE="${AWS_PROFILE:-sandeep}"
AWS_REGION="${AWS_REGION:-us-east-2}"
ECR_REGISTRY="${ECR_REGISTRY:-321573752629.dkr.ecr.us-east-2.amazonaws.com}"
ECR_REPO="${ECR_REPO:-agentcore}"

LOCAL_IMAGE="${TAG}:local"
REMOTE_IMAGE="${ECR_REGISTRY}/${ECR_REPO}:${TAG}"

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

if [[ ! -f "${DOCKERFILE}" ]]; then
  echo "Dockerfile not found: ${DOCKERFILE}"
  exit 1
fi

echo "==> Building ${LOCAL_IMAGE} from ${DOCKERFILE} (linux/arm64)"
docker build --platform linux/arm64 -f "${DOCKERFILE}" -t "${LOCAL_IMAGE}" .

echo "==> Tagging ${REMOTE_IMAGE}"
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

echo "==> Logging in to ECR (${AWS_REGION}, profile ${AWS_PROFILE})"
aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

echo "==> Pushing ${REMOTE_IMAGE}"
docker push "${REMOTE_IMAGE}"

DIGEST="$(docker image inspect "${REMOTE_IMAGE}" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"
echo "==> Done"
echo "    URI:    ${REMOTE_IMAGE}"
if [[ -n "${DIGEST}" ]]; then
  echo "    Digest: ${DIGEST}"
fi
echo "Remember to update the AgentCore Runtime so it picks up the new digest."
