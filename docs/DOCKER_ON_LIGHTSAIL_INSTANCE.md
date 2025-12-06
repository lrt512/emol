# Docker on Lightsail Instance

Run eMoL in Docker on your Lightsail instance.

## Why This Approach?

- **Cost**: Use the inexpensive $7/month instance
- **Simplicity**: Install Docker, run containers
- **Benefits**: Easier deployments, rollbacks, consistency

## Resource Requirements

1GB RAM / 2 vCPU is sufficient:
- Container image: ~500MB-1GB
- Running container: ~200-400MB RAM

## Setup

### 1. Install Docker

Add Docker's official repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version
docker compose version
```

### 2. Configure AWS Access

Lightsail's automatic IAM role isn't editable. Use two IAM users:

| User | Purpose | Permissions |
|------|---------|-------------|
| ECR user | Host pulls images | `AmazonEC2ContainerRegistryReadOnly` |
| eMoL service user | Container reads SSM | SSM read access |

**Host credentials (ubuntu user, for ECR):**

```bash
mkdir -p ~/.aws
cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = ECR_USER_ACCESS_KEY
aws_secret_access_key = ECR_USER_SECRET_KEY
EOF

cat > ~/.aws/config << 'EOF'
[default]
region = ca-central-1
EOF

chmod 600 ~/.aws/credentials
```

**Container credentials (eMoL service, for SSM):**

Create `/opt/emol/.env`:

```bash
AWS_ACCESS_KEY_ID=EMOL_SERVICE_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=EMOL_SERVICE_SECRET_KEY
AWS_DEFAULT_REGION=ca-central-1
```

The deploy script ensures this is available to the container via `env_file` in docker-compose.

**Verify ECR access:**

```bash
aws ecr get-login-password --region ca-central-1 | \
    docker login --username AWS --password-stdin \
    <account-id>.dkr.ecr.ca-central-1.amazonaws.com
```

### 3. Deploy

Copy `setup_files/host/deploy-docker.sh` to `/opt/emol/` on the server.

```bash
# Test deployment on port 8080
./deploy-docker.sh --registry <account-id>.dkr.ecr.ca-central-1.amazonaws.com --test

# Verify at http://your-server:8080

# Cutover to port 80
./deploy-docker.sh --registry <account-id>.dkr.ecr.ca-central-1.amazonaws.com --cutover
```

## docker-compose.prod.yml

Create from the example:

```bash
cp docker-compose.prod.yml.example docker-compose.prod.yml
```

The deploy script updates the image tag automatically.

## Updating

```bash
./deploy-docker.sh --registry <account-id>.dkr.ecr.ca-central-1.amazonaws.com
```

## Monitoring

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
docker stats
```

## SSL/HTTPS

Run certbot on the host and proxy to the container, or handle SSL at a load balancer.

## Troubleshooting

**ECR access denied?**
- Check `~/.aws/credentials` exists for ubuntu user
- Verify ECR IAM user has `AmazonEC2ContainerRegistryReadOnly` policy

**SSM access denied in container?**
- Check `/opt/emol/.env` has service user credentials
- Verify eMoL service IAM user has SSM read permissions

**Container won't start?**
```bash
docker compose -f docker-compose.prod.yml logs
free -h
```

## Checklist

- [ ] Install Docker
- [ ] Configure ECR credentials (`~/.aws/credentials`)
- [ ] Configure service credentials (`/opt/emol/.env`)
- [ ] Copy deploy script to server
- [ ] Create docker-compose.prod.yml
- [ ] Test on port 8080
- [ ] Cutover to port 80
- [ ] Verify cron jobs running
