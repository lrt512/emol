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

AWS CLI v2 automatically uses the credential chain (IAM roles, SSO, environment variables, etc.).

**Option A: IAM Role (Recommended)**

If your Lightsail instance has an IAM role attached with ECR read permissions, AWS CLI v2 will use it automatically. No credential files needed!

**Option B: IAM User Credentials**

If you need to use IAM user credentials, create `~/.aws/config`:

```bash
mkdir -p ~/.aws
cat > ~/.aws/config << 'EOF'
[default]
region = ca-central-1
EOF
```

Then configure credentials using one of:
- `aws configure` (interactive)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- SSO (`aws sso login`)

**Container credentials (eMoL service, for SSM):**

Create `/home/ubuntu/emol/.env`:

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

If this works, your AWS credentials are configured correctly.

### 3. Install AWS CLI v2 (if needed)

```bash
# Check if already installed
aws --version

# If not installed, download and install:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 4. Deploy

Copy `setup_files/host/deploy-docker.sh` to `/home/ubuntu/emol/` on the server.

```bash
# Test deployment on port 8080
./deploy-docker.sh --registry <account-id>.dkr.ecr.ca-central-1.amazonaws.com --test

# Verify at http://your-server:8080

# Cutover to port 80
./deploy-docker.sh --registry <account-id>.dkr.ecr.ca-central-1.amazonaws.com --cutover
```

## docker-compose.prod.yml

Create from the example in `/home/ubuntu/emol/`:

```bash
cd /home/ubuntu/emol
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
- Verify AWS CLI v2 is installed: `aws --version`
- Check credential chain: `aws sts get-caller-identity`
- If using IAM role: Verify role has `AmazonEC2ContainerRegistryReadOnly` policy
- If using IAM user: Run `aws configure` or set environment variables
- Test ECR access: `aws ecr describe-repositories --region ca-central-1`

**SSM access denied in container?**
- Check `/home/ubuntu/emol/.env` has service user credentials
- Verify eMoL service IAM user/role has SSM read permissions

**Container won't start?**
```bash
docker compose -f docker-compose.prod.yml logs
free -h
```

## Checklist

- [ ] Install Docker
- [ ] Install AWS CLI v2 (if not already installed)
- [ ] Configure AWS access (IAM role or user credentials)
- [ ] Verify ECR access: `aws ecr get-login-password --region ca-central-1`
- [ ] Configure service credentials (`/home/ubuntu/emol/.env`)
- [ ] Copy deploy script to server
- [ ] Create docker-compose.prod.yml
- [ ] Test on port 8080
- [ ] Cutover to port 80
- [ ] Verify cron jobs running
