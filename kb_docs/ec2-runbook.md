# EC2 ops runbook

## What EC2 is (ops view)
Amazon EC2 is virtual servers (instances) you manage: OS, patches, scaling (unless using Auto Scaling), and often SSH/SSM access.

## Common checks when an app is "down"
1. Instance state is `running` in the EC2 console.
2. Status checks: both system and instance checks should be OK.
3. Security group allows the expected inbound ports (e.g. 80/443) from the right source.
4. Confirm the process is listening (`ss -lntp` or app health endpoint).
5. Check disk: full disk often causes cryptic app failures (`df -h`).

## Access
Prefer **SSM Session Manager** over opening SSH to the world.
If SSH is required, restrict to bastion or known CIDRs only.

## AMI / rebuild
If the instance is unhealthy and disposable:
1. Launch replacement from the known-good AMI or launch template.
2. Attach the same IAM instance profile and security groups.
3. Update DNS/target group to the new instance.
4. Terminate the old instance after verification.

## Tags we expect
- `Environment` = lab|dev|prod
- `Owner` = team or person
- `Service` = application name
