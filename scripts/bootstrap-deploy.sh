#!/bin/bash

# Bootstrap Deployment Script
# Copies necessary deployment files to the remote Lightsail instance

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

show_help() {
    cat << EOF
eMoL Deployment Bootstrap

Copies deployment scripts and configuration templates to a remote server.

Usage: $0 [options] <user@host>

Options:
    --key-file PATH     Path to SSH private key
    --help              Show this help message

Example:
    $0 ubuntu@192.168.1.5
    $0 --key-file ~/.ssh/my-key.pem ubuntu@emol.ealdormere.ca
EOF
    exit 0
}

SSH_KEY=""
REMOTE_HOST=""

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --key-file)
            SSH_KEY="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${RESET}"
            show_help
            ;;
        *)
            if [ -z "$REMOTE_HOST" ]; then
                REMOTE_HOST="$1"
                shift
            else
                echo -e "${RED}Unexpected argument: $1${RESET}"
                show_help
            fi
            ;;
    esac
done

if [ -z "$REMOTE_HOST" ]; then
    echo -e "${RED}Error: Remote host is required${RESET}"
    show_help
fi

# Build SSH/SCP command prefix
SSH_OPTS="-o StrictHostKeyChecking=no"
if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh $SSH_OPTS -i $SSH_KEY"
    SCP_CMD="scp $SSH_OPTS -i $SSH_KEY"
else
    SSH_CMD="ssh $SSH_OPTS"
    SCP_CMD="scp $SSH_OPTS"
fi

echo -e "${YELLOW}Bootstrapping deployment on ${REMOTE_HOST}...${RESET}"

# 1. Create remote directories
echo -e "Creating remote directories..."
$SSH_CMD "$REMOTE_HOST" "mkdir -p ~/emol && sudo mkdir -p /opt/emol_config && sudo chown \$USER:\$USER /opt/emol_config"

# 2. Copy files
echo -e "Copying deployment files..."
FILES_TO_COPY=(
    "scripts/deploy-docker.sh"
    "scripts/generate-compose.py"
    "docker-compose.prod.yml.example"
    "docker-compose.test.yml.example"
    "docs/DEPLOYMENT.md"
)

for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$file" ]; then
        $SCP_CMD "$file" "${REMOTE_HOST}:~/emol/"
    else
        echo -e "${RED}Warning: Local file $file not found, skipping.${RESET}"
    fi
done

# 3. Set permissions
echo -e "Setting permissions..."
$SSH_CMD "$REMOTE_HOST" "chmod +x ~/emol/deploy-docker.sh ~/emol/generate-compose.py"

# 4. Create config directory info
echo -e "Configuration directory created at /opt/emol_config"
echo -e "Place the following files there (optional):"
echo -e "  - /opt/emol_config/emol_production.py (Django production settings override)"
echo -e "  - /opt/emol_config/emol_credentials.json (AWS credentials)"

echo -e "${GREEN}Bootstrap complete!${RESET}"
echo -e "You can now run deployment on the server:"
echo -e "  ssh ${REMOTE_HOST}"
echo -e "  cd ~/emol"
echo -e "  ./deploy-docker.sh --help"

