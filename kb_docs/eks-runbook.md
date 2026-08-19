# EKS ops runbook

## What EKS is (ops view)
Amazon EKS is managed Kubernetes. You manage workloads (Deployments, Services, Ingress); AWS manages the control plane.

## Quick triage when a service is unreachable
1. `kubectl get pods -n <namespace>` — are pods Running?
2. `kubectl describe pod <name> -n <namespace>` — look for ImagePullBackOff, CrashLoopBackOff, OOMKilled.
3. `kubectl logs <pod> -n <namespace> --tail=200`
4. Check Service and Endpoints — empty endpoints mean no ready pods.
5. Check Ingress/ALB annotations and security groups if traffic enters via load balancer.

## Image pull issues
- Confirm the node/pod role can pull from ECR (`ecr:GetAuthorizationToken`, image pull permissions).
- Confirm the image tag/digest exists in the correct region/account.
- Prefer immutable digests for production deploys.

## Deploy safely
1. Update the Deployment image.
2. Watch rollout: `kubectl rollout status deployment/<name> -n <namespace>`
3. If bad: `kubectl rollout undo deployment/<name> -n <namespace>`

## Capacity
If pods stay Pending:
- Check node CPU/memory pressure.
- Check taints/tolerations and node selectors.
- For Cluster Autoscaler setups, confirm new nodes can join.
