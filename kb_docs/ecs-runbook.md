# ECS ops runbook

## What ECS is (ops view)
Amazon ECS runs containers on either **Fargate** (serverless tasks) or **EC2 capacity**. Most lab/prod APIs use a **Service** that keeps N tasks healthy behind a load balancer.

## Deploy a new image
1. Build and push the image to ECR (tag carefully; avoid overwriting unrelated apps with `:latest` if multiple apps share a repo).
2. Update the task definition with the new image URI/digest.
3. Update the ECS service to use the new task definition revision.
4. Watch deployment events until old tasks drain and new tasks are steady.

## Health check failures
If tasks start then die:
1. Read the stopped task reason in ECS (essential container exited, ELB health check failed, etc.).
2. Check CloudWatch Logs for the task log group.
3. Confirm container port matches target group port.
4. Confirm security groups: ALB → tasks, and tasks → dependencies (DB, APIs).
5. Confirm CPU/memory are not too low (OOM kills look like random restarts).

## Rollback
1. Update the service to the previous task definition revision.
2. Confirm healthy task count returns.
3. Record the bad image digest so it is not redeployed by mistake.

## AgentCore vs ECS (lab note)
AgentCore Runtime hosts agent containers for you. ECS is still the general AWS pattern for long-running container services. Concepts (image, health, logs, rollback) transfer.
