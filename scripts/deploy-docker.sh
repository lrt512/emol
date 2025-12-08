#!/bin/bash

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

REPO_NAME="emol"
REGION="ca-central-1"
EMOL_HOME="${HOME}/emol"
CONFIG_DIR="/opt/emol_config"
COMPOSE_PROD="${EMOL_HOME}/docker-compose.prod.yml"
COMPOSE_TEST="${EMOL_HOME}/docker-compose.test.yml"
COMPOSE_PROD_EXAMPLE="${EMOL_HOME}/docker-compose.prod.yml.example"
COMPOSE_TEST_EXAMPLE="${EMOL_HOME}/docker-compose.test.yml.example"

show_help() {
    cat << EOF
eMoL Docker Deployment Script

Deploys eMoL container on Lightsail instance using Docker Compose.

Usage: $0 [options]

Options:
    --registry REGISTRY    ECR registry URL (e.g., 123456789012.dkr.ecr.ca-central-1.amazonaws.com)
    --version VERSION      Specific version to deploy (default: latest from ECR or latest tag)
    --test                 Deploy on port 8080 for testing (keeps existing service on port 80)
    --cutover              Switch to port 80 and stop old service (final deployment)
    --dry-run             Show what would be done without deploying
    --help                Show this help message

Examples:
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --test    # Test on 8080
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --cutover # Final cutover to 80
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com --version v1.3.0
EOF
    exit 0
}

get_current_version() {
    local registry=$1
    
    if [ -n "${registry}" ]; then
        echo -e "${YELLOW}Checking ECR for latest version...${RESET}"
        local latest_tag=$(aws ecr describe-images \
            --repository-name ${REPO_NAME} \
            --region ${REGION} \
            --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' \
            --output text 2>/dev/null | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        
        if [ -n "${latest_tag}" ] && [ "${latest_tag}" != "None" ]; then
            echo "${latest_tag}" | sed 's/^v//'
            return 0
        fi
    fi
    
    if [ -f "${EMOL_HOME}/VERSION" ]; then
        cat "${EMOL_HOME}/VERSION"
    else
        echo "latest"
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
        echo -e "${YELLOW}Test mode: Keeping production service running on port 80${RESET}"
        if [ -f "${COMPOSE_TEST}" ]; then
            cd "${EMOL_HOME}"
            docker-compose -f docker-compose.test.yml down 2>/dev/null || true
        fi
        return 0
    fi
    
    echo -e "${YELLOW}Stopping old services...${RESET}"
    
    if systemctl is-active --quiet emol 2>/dev/null; then
        echo "Stopping systemd emol service..."
        sudo systemctl stop emol || true
    fi
    
    if [ -f "${COMPOSE_PROD}" ]; then
        cd "${EMOL_HOME}"
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    fi
    
    if [ -f "${COMPOSE_TEST}" ]; then
        cd "${EMOL_HOME}"
        docker-compose -f docker-compose.test.yml down 2>/dev/null || true
    fi
}

ensure_compose_file() {
    local compose_file=$1
    local compose_example=$2
    local file_type=$3
    
    if [ ! -d "${EMOL_HOME}" ]; then
        echo -e "${YELLOW}Creating ${EMOL_HOME}...${RESET}"
        mkdir -p "${EMOL_HOME}"
    fi
    
    if [ ! -f "${compose_file}" ]; then
        if [ -f "${compose_example}" ]; then
            echo -e "${YELLOW}Creating ${file_type} from example...${RESET}"
            cp "${compose_example}" "${compose_file}"
        else
            echo -e "${RED}Error: ${compose_example} not found${RESET}"
            echo -e "${YELLOW}Please ensure ${file_type}.example is in ${EMOL_HOME}${RESET}"
            exit 1
        fi
    fi
}

update_compose_file() {
    local registry=$1
    local version=$2
    
    echo -e "${YELLOW}Updating Docker Compose configuration...${RESET}"
    
    local image_tag="${registry}/${REPO_NAME}:${version}"
    local compose_file
    
    if [ "${TEST_MODE}" = true ]; then
        compose_file="${COMPOSE_TEST}"
        ensure_compose_file "${COMPOSE_TEST}" "${COMPOSE_TEST_EXAMPLE}" "docker-compose.test.yml"
    else
        compose_file="${COMPOSE_PROD}"
        ensure_compose_file "${COMPOSE_PROD}" "${COMPOSE_PROD_EXAMPLE}" "docker-compose.prod.yml"
    fi
    
    sed -i "s|image:.*|image: ${image_tag}|" "${compose_file}"
    
    # Mount configuration files from /opt/emol_config if they exist
    if [ -f "${CONFIG_DIR}/emol_production.py" ]; then
        echo -e "${YELLOW}Mounting custom production settings...${RESET}"
        # Add or update the settings mount
        if grep -q "# - .*emol_production.py" "${compose_file}"; then
            sed -i "s|# - .*emol_production.py|- ${CONFIG_DIR}/emol_production.py:/opt/emol/emol/emol/settings/emol_production.py:ro|" "${compose_file}"
        elif ! grep -q "${CONFIG_DIR}/emol_production.py" "${compose_file}"; then
            # Add it after the nginx_logs volume line
            sed -i "/nginx_logs:/a\      - ${CONFIG_DIR}/emol_production.py:/opt/emol/emol/emol/settings/emol_production.py:ro" "${compose_file}"
        fi
    fi
    
    if [ -f "${CONFIG_DIR}/emol_credentials.json" ]; then
        echo -e "${YELLOW}Mounting AWS credentials...${RESET}"
        # Mount credentials file (application will need to handle JSON format)
        if grep -q "# - .*emol_credentials.json" "${compose_file}"; then
            sed -i "s|# - .*emol_credentials.json|- ${CONFIG_DIR}/emol_credentials.json:/opt/emol/emol_credentials.json:ro|" "${compose_file}"
        elif ! grep -q "${CONFIG_DIR}/emol_credentials.json" "${compose_file}"; then
            sed -i "/nginx_logs:/a\      - ${CONFIG_DIR}/emol_credentials.json:/opt/emol/emol_credentials.json:ro" "${compose_file}"
        fi
    fi
    
    echo -e "${GREEN}Updated image to: ${image_tag}${RESET}"
}

start_container() {
    local compose_file
    local compose_name
    
    if [ "${TEST_MODE}" = true ]; then
        compose_file="docker-compose.test.yml"
        compose_name="test"
    else
        compose_file="docker-compose.prod.yml"
        compose_name="production"
    fi
    
    echo -e "${YELLOW}Starting ${compose_name} container...${RESET}"
    cd "${EMOL_HOME}"
    docker-compose -f "${compose_file}" up -d
    
    echo -e "${YELLOW}Waiting for container to be healthy...${RESET}"
    sleep 5
    
    if docker-compose -f "${compose_file}" ps | grep -q "Up"; then
        echo -e "${GREEN}Container started successfully${RESET}"
    else
        echo -e "${RED}Container failed to start${RESET}"
        docker-compose -f "${compose_file}" logs
        exit 1
    fi
}

show_status() {
    local compose_file
    
    if [ "${TEST_MODE}" = true ]; then
        compose_file="docker-compose.test.yml"
    else
        compose_file="docker-compose.prod.yml"
    fi
    
    echo -e "\n${GREEN}=== Container Status ===${RESET}"
    cd "${EMOL_HOME}"
    docker-compose -f "${compose_file}" ps
    
    echo -e "\n${GREEN}=== Recent Logs ===${RESET}"
    docker-compose -f "${compose_file}" logs --tail=20
}

cleanup_old_images() {
    echo -e "${YELLOW}Cleaning up old images...${RESET}"
    docker image prune -f
}

DRY_RUN=false
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

# Ensure config directory exists
if [ ! -d "${CONFIG_DIR}" ]; then
    echo -e "${YELLOW}Creating configuration directory ${CONFIG_DIR}...${RESET}"
    sudo mkdir -p "${CONFIG_DIR}"
    sudo chown ${USER}:${USER} "${CONFIG_DIR}"
fi

if [ -z "${VERSION}" ]; then
    if [ -n "${REGISTRY}" ]; then
        VERSION=$(get_current_version "${REGISTRY}")
    else
        VERSION="latest"
    fi
    echo -e "${GREEN}Using version: ${VERSION}${RESET}"
fi

if [ "${VERSION}" != "latest" ] && [[ ! "${VERSION}" =~ ^v ]]; then
    VERSION="v${VERSION}"
fi

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would deploy version: ${VERSION}${RESET}"
    if [ -n "${REGISTRY}" ]; then
        echo -e "${YELLOW}[DRY RUN] Would pull from: ${REGISTRY}/${REPO_NAME}:${VERSION}${RESET}"
    fi
    exit 0
fi

if [ -z "${REGISTRY}" ]; then
    echo -e "${RED}Error: --registry is required${RESET}"
    show_help
fi

login_to_ecr ${REGISTRY}
pull_image ${REGISTRY} ${VERSION}
update_compose_file ${REGISTRY} ${VERSION}

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
    echo -e "\n${YELLOW}Next steps:${RESET}"
    echo -e "  1. Verify the container is working correctly"
    echo -e "  2. Archive the old installation at /opt/emol (if desired)"
    echo -e "  3. Update any monitoring/backup scripts to use ${EMOL_HOME}"
else
    echo -e "\n${GREEN}Deployment complete!${RESET}"
fi

    if [ "${TEST_MODE}" = true ]; then
        echo -e "\nView logs: cd ${EMOL_HOME} && docker-compose -f docker-compose.test.yml logs -f"
        echo -e "Stop container: cd ${EMOL_HOME} && docker-compose -f docker-compose.test.yml down"
    else
        echo -e "\nView logs: cd ${EMOL_HOME} && docker-compose -f docker-compose.prod.yml logs -f"
        echo -e "Stop container: cd ${EMOL_HOME} && docker-compose -f docker-compose.prod.yml down"
    fi

