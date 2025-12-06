# Setup Files Directory

Scripts and configuration for deploying and managing eMoL containers.

## Scripts

### Production Deployment

- **`build-and-push.sh`** — Build container image and push to ECR (run on dev machine)
- **`host/deploy-docker.sh`** — Pull image from ECR and deploy on Lightsail (copy to production server)
- **`docker-entrypoint-prod.sh`** — Production container entrypoint (runs migrations, cron, gunicorn, nginx)

### Development

- **`docker-entrypoint-dev.sh`** — Development container entrypoint (runs migrations, superuser, gunicorn with log tailing)

## Configuration Files

- **`configs/`** — Nginx and gunicorn configurations
- **`localstack/`** — LocalStack SSM parameter seeding for development
- **`mysql/`** — MySQL initialization scripts for development

## Deployment Workflow

### Build and Push (Dev Machine)

```bash
./setup_files/build-and-push.sh --account-id <aws-account-id>
```

### Deploy (Production Server)

```bash
./setup_files/host/deploy-docker.sh --registry <ecr-registry-url>
```

### Test Before Cutover

```bash
./setup_files/host/deploy-docker.sh --registry <ecr-url> --test  # Runs on port 8080
./setup_files/host/deploy-docker.sh --registry <ecr-url> --cutover  # Switch to port 80
```
