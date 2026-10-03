# Deploy Liwin AI on AWS

This template deploys the FastAPI application as one ECS Fargate task. It keeps
the ChromaDB index and SQLite conversation memory on Amazon EFS, so a task
replacement does not erase the knowledge index or chat history.

## Required AWS resources

1. An Amazon ECR repository named `liwin-ai`.
2. An Amazon ECS cluster and Fargate service with desired count set to `1`.
3. An Amazon EFS file system and access point, reachable from the ECS task
   security group on NFS port `2049`.
4. A Secrets Manager secret containing only the Gemini API key.
5. A CloudWatch log group named `/ecs/liwin-ai`.
6. An Application Load Balancer, an ACM certificate, and a Route 53 DNS record
   if a custom HTTPS domain is required.

## Build and publish the image

Authenticate Docker to ECR, then build and tag the image for your repository.
Do this from the repository root after replacing the placeholders below:

```powershell
aws ecr get-login-password --region <AWS_REGION> |
  docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com

docker build -t liwin-ai .
docker tag liwin-ai:latest <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/liwin-ai:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/liwin-ai:latest
```

## Register the task

Copy `task-definition.template.json` to a non-committed local file, replace all
angle-bracket placeholders, then register it:

```powershell
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

The task execution role needs permission to pull from ECR and write CloudWatch
logs. The task role needs `secretsmanager:GetSecretValue` for the single Gemini
secret and EFS client mount/write permissions for its access point.

## Important operating notes

- Never commit `.env`, a Gemini key, local `chroma_db/`, or `liwin_memory.db`.
- The application creates its initial ChromaDB index on the first task start.
  Keep `desiredCount` at `1`, because local SQLite memory is not safe for
  multiple concurrent writers.
- Back up EFS before changing the knowledge base or re-indexing production.
- Configure the load balancer health check to request `/health`.
