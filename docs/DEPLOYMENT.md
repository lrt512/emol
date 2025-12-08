# eMoL Deployment Guide

This guide covers the deployment workflow for eMoL using Docker containers on AWS Lightsail.

## Prerequisites

-   **AWS Account**: With permissions to access ECR and SSM Parameter Store.
-   **Lightsail Instance**: Running Ubuntu 22.04 with Docker and Docker Compose installed.
-   **SSM Parameters**: Database credentials and secrets configured (see below).

## 1. Build and Push (Local Development)

On your development machine, tag and push the new version:

```bash
# 1. Tag your release
git tag v1.3.0
git push --tags

# 2. Build and push to ECR
# This builds Dockerfile.prod and pushes tags: latest, v1.3.0
./setup_files/build-and-push.sh --account-id <aws-account-id>
```

## 2. Deployment Strategy

We use a blue/green-style deployment strategy to ensure zero downtime and safe testing:

1.  **Test Deployment**: Deploy the new version on port **8080** alongside the running production version.
2.  **Verification**: Confirm functionality on the test port.
3.  **Cutover**: Switch production traffic to the new container on port **80** and stop the old one.

### Step 1: Test Deployment

On your production server, deploy the new version to the test port:

```bash
cd ~/emol
# Deploys version from ECR (latest or specific) to port 8080
./setup_files/host/deploy-docker.sh --registry <ecr-url> --test
```

**Note**: This uses `docker-compose.test.yml` and keeps your existing production service (port 80) running uninterrupted.

### Step 2: Verification

Access `http://your-server:8080` and verify the following:

-   [ ] **Login**: Can you authenticate via Google SSO?
-   [ ] **Data**: Do combatant cards display correctly?
-   [ ] **Admin**: Can you access the admin interface?
-   [ ] **Static Files**: Do CSS and images load properly?
-   [ ] **Logs**: Check for errors:
    ```bash
    docker compose -f docker-compose.test.yml logs -f
    ```

### Step 3: Production Cutover

Once testing is successful, promote the container to production:

```bash
# Stops test container (8080) and old production container (80)
# Starts new version on port 80
./setup_files/host/deploy-docker.sh --registry <ecr-url> --cutover
```

## Rollback Procedures

If issues arise after cutover, you can quickly rollback.

### Rolling back to a previous version

```bash
# Deploy a specific previous version tag
./setup_files/host/deploy-docker.sh --registry <ecr-url> --version v1.2.9 --cutover
```

### Emergency Revert (If migrating from legacy systemd)

If you just migrated from the legacy systemd setup and need to go back:

```bash
cd ~/emol
docker compose -f docker-compose.prod.yml down
sudo systemctl start emol nginx
```

## Configuration & Management

### Configuration Files

Instance-specific configuration files should be placed in `/opt/emol_config/` on the server:

*   **`/opt/emol_config/emol_production.py`** (optional): Django settings overrides for production. This file will be mounted into the container and can override settings from `emol.settings.prod`.
*   **`/opt/emol_config/emol_credentials.json`** (optional): AWS credentials in JSON format. This file will be mounted into the container for the application to use.

The deployment script automatically detects these files and mounts them into the container if they exist.

### SSM Parameters

Ensure these parameters exist in AWS Systems Manager (SSM) Parameter Store (`SecureString`):

```bash
/emol/django_settings_module : emol.settings.prod
/emol/oauth_client_id        : <google-oauth-id>
/emol/oauth_client_secret    : <google-oauth-secret>
/emol/secret_key             : <django-secret-key>
/emol/db_host                : <db-host>
/emol/db_name                : <db-name>
/emol/db_user                : <db-user>
/emol/db_password            : <db-password>
```

### Monitoring & Logs

**Production Logs**:
```bash
cd ~/emol
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

**Resource Usage**:
```bash
docker stats
```

**Container Status**:
```bash
docker compose -f docker-compose.prod.yml ps
```

### Resource Management Notes

The Lightsail instance has 1GB of RAM.
-   **Testing Mode**: Running both Test (8080) and Prod (80) simultaneously is tight. Monitor memory usage (`free -h`) during testing.
-   **Cleanup**: The deployment script attempts to prune unused images, but periodic `docker system prune` may be helpful.

## Container Internals

The production entrypoint (`docker-entrypoint-prod.sh`) handles startup automation:

1.  **Nginx**: Configures and starts Nginx as a reverse proxy.
2.  **Database**: Waits for MySQL, runs `migrate`.
3.  **Assets**: Runs `collectstatic`.
4.  **Cache**: Creates database cache table if missing.
5.  **Cron**: Sets up background tasks (reminders, cleanup).
6.  **Gunicorn**: Starts the application server with 2 workers.
