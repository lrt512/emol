# eMoL Deployment

eMoL runs in Docker containers. This guide covers production deployment.

## Prerequisites

- AWS account with ECR access
- Lightsail instance (or similar) with Docker installed
- SSM parameters configured (see below)

## Build and Push

On your development machine:

```bash
./setup_files/build-and-push.sh --account-id <aws-account-id>
```

This builds `Dockerfile.prod` and pushes to ECR.

## Deploy

Copy `setup_files/host/deploy-docker.sh` to your production server, then:

```bash
# Test on port 8080 first (keeps existing service on 80)
./deploy-docker.sh --registry <ecr-url> --test

# Verify at http://your-server:8080

# Cutover to port 80
./deploy-docker.sh --registry <ecr-url> --cutover
```

## SSM Parameters

Configure these in AWS SSM Parameter Store:

```bash
aws ssm put-parameter --name "/emol/django_settings_module" --value "emol.settings.prod" --type "SecureString"
aws ssm put-parameter --name "/emol/oauth_client_id" --value "<your-oauth-id>" --type "SecureString"
aws ssm put-parameter --name "/emol/oauth_client_secret" --value "<your-oauth-secret>" --type "SecureString"
aws ssm put-parameter --name "/emol/db_host" --value "<your-db-host>" --type "SecureString"
aws ssm put-parameter --name "/emol/db_name" --value "<your-db-name>" --type "SecureString"
aws ssm put-parameter --name "/emol/db_user" --value "<your-db-user>" --type "SecureString"
aws ssm put-parameter --name "/emol/db_password" --value "<your-db-password>" --type "SecureString"
```

## Container Startup

The production container (`docker-entrypoint-prod.sh`) automatically:

1. Configures nginx
2. Runs database migrations
3. Collects static files
4. Creates cache table
5. Sets up cron jobs (send_reminders at 3 AM, clean_expired at 4 AM)
6. Starts gunicorn and nginx

## Rollback

Keep the previous image tag. To rollback:

```bash
./deploy-docker.sh --registry <ecr-url> --version <previous-version>
```

## Monitoring

```bash
# Container status
docker compose -f docker-compose.prod.yml ps

# Logs
docker compose -f docker-compose.prod.yml logs -f

# Resource usage
docker stats
```

## SSL/HTTPS

Run certbot on the host and proxy to the container, or configure SSL termination at a load balancer.
