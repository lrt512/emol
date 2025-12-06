#!/bin/bash

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

REPO_NAME="emol"
REGION="ca-central-1"
COMPOSE_FILE="/opt/emol/docker-compose.prod.yml"

show_help() {
    cat << EOF
eMoL Docker Deployment Script

Deploys eMoL container on Lightsail instance using Docker Compose.

Usage: $0 [options]

Options:
    --registry REGISTRY    ECR registry URL (e.g., 123456789012.dkr.ecr.ca-central-1.amazonaws.com)
    --version VERSION      Specific version to deploy (default: from VERSION file)
    --local                Use local image instead of pulling from ECR
    --test                 Deploy on port 8080 for testing (keeps existing service on port 80)
    --cutover              Switch to port 80 and stop old service (final deployment)
    --dry-run             Show what would be done without deploying
    --help                Show this help message

Examples:
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --test    # Test on 8080
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --cutover # Final cutover to 80
    $0 --local --test                                                         # Test with local image
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --version v0.2.0
EOF
    exit 0
}

get_current_version() {
    if [ -f "/opt/emol/VERSION" ]; then
        cat /opt/emol/VERSION
    else
        echo "0.0.0"
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${RESET}"
        echo "Install with: sudo apt-get install -y docker.io docker-compose"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed${RESET}"
        echo "Install with: sudo apt-get install -y docker-compose"
        exit 1
    fi
}

login_to_ecr() {
    local registry=$1
    local account_id=$(echo $registry | cut -d'.' -f1)
    
    echo -e "${YELLOW}Logging in to ECR...${RESET}"
    aws ecr get-login-password --region ${REGION} | \
        docker login --username AWS --password-stdin ${registry}
}

pull_image() {
    local registry=$1
    local version=$2
    
    echo -e "${YELLOW}Pulling image from ECR...${RESET}"
    docker pull ${registry}/${REPO_NAME}:${version} || \
        docker pull ${registry}/${REPO_NAME}:latest
}

stop_old_services() {
    if [ "${TEST_MODE}" = true ]; then
        echo -e "${YELLOW}Test mode: Keeping existing service running on port 80${RESET}"
        return 0
    fi
    
    echo -e "${YELLOW}Stopping old services...${RESET}"
    
    if systemctl is-active --quiet emol 2>/dev/null; then
        echo "Stopping systemd emol service..."
        sudo systemctl stop emol || true
    fi
    
    if [ -f "${COMPOSE_FILE}" ]; then
        cd /opt/emol
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    fi
}

update_compose_file() {
    local registry=$1
    local version=$2
    
    echo -e "${YELLOW}Updating Docker Compose configuration...${RESET}"
    
    if [ ! -f "${COMPOSE_FILE}" ]; then
        echo -e "${YELLOW}Creating docker-compose.prod.yml from example...${RESET}"
        cp /opt/emol/docker-compose.prod.yml.example ${COMPOSE_FILE}
    fi
    
    local image_tag="${registry}/${REPO_NAME}:${version}"
    
    sed -i "s|image:.*|image: ${image_tag}|" ${COMPOSE_FILE}
    
    if [ "${TEST_MODE}" = true ]; then
        echo -e "${YELLOW}Test mode: Setting port to 8080${RESET}"
        if grep -q '"- "80:80"' ${COMPOSE_FILE} || grep -q '"- 80:80"' ${COMPOSE_FILE}; then
            sed -i 's|- "80:80"|- "8080:80"|' ${COMPOSE_FILE}
            sed -i 's|- 80:80|- "8080:80"|' ${COMPOSE_FILE}
        fi
        if grep -q '# - "80:80"' ${COMPOSE_FILE}; then
            sed -i 's|# - "80:80"|- "8080:80"|' ${COMPOSE_FILE}
        fi
    elif [ "${CUTOVER_MODE}" = true ]; then
        echo -e "${YELLOW}Cutover mode: Setting port to 80${RESET}"
        if grep -q '"- "8080:80"' ${COMPOSE_FILE} || grep -q '"- 8080:80"' ${COMPOSE_FILE}; then
            sed -i 's|- "8080:80"|- "80:80"|' ${COMPOSE_FILE}
            sed -i 's|- 8080:80|- "80:80"|' ${COMPOSE_FILE}
        fi
        if grep -q '# - "80:80"' ${COMPOSE_FILE}; then
            sed -i 's|# - "80:80"|- "80:80"|' ${COMPOSE_FILE}
        fi
    fi
    
    echo -e "${GREEN}Updated image to: ${image_tag}${RESET}"
}

start_container() {
    echo -e "${YELLOW}Starting container...${RESET}"
    cd /opt/emol
    docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${YELLOW}Waiting for container to be healthy...${RESET}"
    sleep 5
    
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${GREEN}Container started successfully${RESET}"
    else
        echo -e "${RED}Container failed to start${RESET}"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

show_status() {
    echo -e "\n${GREEN}=== Container Status ===${RESET}"
    cd /opt/emol
    docker-compose -f docker-compose.prod.yml ps
    
    echo -e "\n${GREEN}=== Recent Logs ===${RESET}"
    docker-compose -f docker-compose.prod.yml logs --tail=20
}

cleanup_old_images() {
    echo -e "${YELLOW}Cleaning up old images...${RESET}"
    docker image prune -f
}

DRY_RUN=false
USE_LOCAL=false
TEST_MODE=false
CUTOVER_MODE=false
REGISTRY=""
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            REGISTRY=$2
            shift 2
            ;;
        --version)
            VERSION=$2
            shift 2
            ;;
        --local)
            USE_LOCAL=true
            shift
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --cutover)
            CUTOVER_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${RESET}"
            show_help
            ;;
    esac
done

if [ "${TEST_MODE}" = true ] && [ "${CUTOVER_MODE}" = true ]; then
    echo -e "${RED}Error: Cannot use --test and --cutover together${RESET}"
    exit 1
fi

check_docker

if [ -z "${VERSION}" ]; then
    VERSION=$(get_current_version)
fi

VERSION="v${VERSION}"

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would deploy version: ${VERSION}${RESET}"
    if [ "${USE_LOCAL}" = false ] && [ -n "${REGISTRY}" ]; then
        echo -e "${YELLOW}[DRY RUN] Would pull from: ${REGISTRY}/${REPO_NAME}:${VERSION}${RESET}"
    else
        echo -e "${YELLOW}[DRY RUN] Would use local image${RESET}"
    fi
    exit 0
fi

if [ "${USE_LOCAL}" = false ]; then
    if [ -z "${REGISTRY}" ]; then
        echo -e "${RED}Error: --registry is required (or use --local)${RESET}"
        show_help
    fi
    
    login_to_ecr ${REGISTRY}
    pull_image ${REGISTRY} ${VERSION}
    update_compose_file ${REGISTRY} ${VERSION}
else
    echo -e "${YELLOW}Using local image: ${REPO_NAME}:${VERSION}${RESET}"
    if [ -f "${COMPOSE_FILE}" ]; then
        sed -i "s|image:.*|image: ${REPO_NAME}:${VERSION}|" ${COMPOSE_FILE}
    fi
fi

stop_old_services
start_container
cleanup_old_images
show_status

if [ "${TEST_MODE}" = true ]; then
    echo -e "\n${GREEN}Test deployment complete!${RESET}"
    echo -e "${YELLOW}Container is running on port 8080${RESET}"
    echo -e "${YELLOW}Existing service is still running on port 80${RESET}"
    echo -e "\n${YELLOW}Note: Running both services uses more resources.${RESET}"
    echo -e "${YELLOW}Monitor with: docker stats && free -h${RESET}"
    echo -e "\nTest the container:"
    echo -e "  http://your-server-ip:8080"
    echo -e "  or"
    echo -e "  http://your-domain:8080"
    echo -e "\nWhen ready to cutover, run:"
    echo -e "  $0 --registry ${REGISTRY:-<registry-url>} --cutover"
    echo -e "\nTo stop old service and save resources:"
    echo -e "  sudo systemctl stop emol nginx"
elif [ "${CUTOVER_MODE}" = true ]; then
    echo -e "\n${GREEN}Cutover complete! Container is now serving on port 80${RESET}"
    echo -e "${YELLOW}Old service has been stopped${RESET}"
else
    echo -e "\n${GREEN}Deployment complete!${RESET}"
fi

echo -e "\nView logs: docker-compose -f ${COMPOSE_FILE} logs -f"
echo -e "Stop container: docker-compose -f ${COMPOSE_FILE} down"

