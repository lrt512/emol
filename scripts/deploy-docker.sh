#!/bin/bash

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

REPO_NAME="emol"
REGION="ca-central-1"

# Determine the actual user's home directory (handles sudo)
if [ -n "${SUDO_USER}" ]; then
    ACTUAL_HOME=$(getent passwd "${SUDO_USER}" | cut -d: -f6)
else
    ACTUAL_HOME="${HOME}"
fi

EMOL_HOME="${ACTUAL_HOME}/emol"
CONFIG_DIR="/opt/emol_config"
CREDENTIALS_FILE="${CONFIG_DIR}/emol_credentials.json"
COMPOSE_PROD="${EMOL_HOME}/docker-compose.prod.yml"
COMPOSE_TEST="${EMOL_HOME}/docker-compose.test.yml"

show_help() {
    cat << EOF
eMoL Docker Deployment Script

Deploys eMoL container on Lightsail instance using Docker Compose.

Usage: $0 [options]

Options:
    --account ACCOUNT_ID   AWS account ID (e.g., 123456789012)
    --version VERSION      Specific version to deploy (default: latest from ECR or latest tag)
    --test                 Deploy on port 8080 for testing (allows latest beta if version unspecified)
    --cutover              Switch to port 80 and stop old service (final deployment)
    --dry-run             Show what would be done without deploying
    --help                Show this help message

Examples:
    $0 --account 123456789012 --test    # Test on 8080
    $0 --account 123456789012 --cutover # Final cutover to 80
    $0 --account 123456789012 --version v1.3.0
EOF
    exit 0
}

load_aws_credentials() {
    if [ ! -f "${CREDENTIALS_FILE}" ]; then
        echo -e "${RED}Error: Credentials file not found: ${CREDENTIALS_FILE}${RESET}"
        echo -e "${YELLOW}Please ensure emol_credentials.json exists in ${CONFIG_DIR}${RESET}"
        exit 1
    fi
    
    echo -e "${YELLOW}Loading AWS credentials from ${CREDENTIALS_FILE}...${RESET}"
    
    export AWS_ACCESS_KEY_ID=$(python3 -c "import json; print(json.load(open('${CREDENTIALS_FILE}'))['aws_access_key_id'])")
    export AWS_SECRET_ACCESS_KEY=$(python3 -c "import json; print(json.load(open('${CREDENTIALS_FILE}'))['aws_secret_access_key'])")
    
    local file_region=$(python3 -c "import json; d=json.load(open('${CREDENTIALS_FILE}')); print(d.get('region_name', ''))" 2>/dev/null || echo "")
    if [ -n "${file_region}" ]; then
        REGION="${file_region}"
        echo -e "${YELLOW}Using region from credentials file: ${REGION}${RESET}"
    fi
    
    export AWS_DEFAULT_REGION="${REGION}"
    
    if [ -z "${AWS_ACCESS_KEY_ID}" ] || [ -z "${AWS_SECRET_ACCESS_KEY}" ]; then
        echo -e "${RED}Error: Invalid credentials file format${RESET}"
        echo -e "${YELLOW}Expected JSON with 'aws_access_key_id' and 'aws_secret_access_key'${RESET}"
        exit 1
    fi
}

build_registry_url() {
    local account_id=$1
    echo "${account_id}.dkr.ecr.${REGION}.amazonaws.com"
}

get_current_version() {
    local registry=$1
    local include_beta=$2
    
    if [ -n "${registry}" ]; then
        echo -e "${YELLOW}Checking ECR for latest version...${RESET}" >&2
        
        # Determine grep pattern based on whether we accept beta versions
        local pattern='^v?[0-9]+\.[0-9]+\.[0-9]+$'
        if [ "${include_beta}" = true ]; then
            pattern='^v?[0-9]+\.[0-9]+\.[0-9]+(-beta\.[0-9]+)?$'
        fi
        
        # Get all tags, filter by pattern, sort and take latest
        local latest_tag=$(aws ecr describe-images \
            --repository-name ${REPO_NAME} \
            --region ${REGION} \
            --query 'imageDetails[*].imageTags[*]' \
            --output text 2>/dev/null | tr '\t' '\n' | grep -E "${pattern}" | sed 's/^v//' | sort -V | tail -1)
        
        if [ -n "${latest_tag}" ] && [ "${latest_tag}" != "None" ]; then
            echo "${latest_tag}"
            return 0
        fi
    fi
    
    # Check for VERSION file, otherwise default to latest
    if [ -f "${EMOL_HOME}/VERSION" ]; then
        local file_version=$(cat "${EMOL_HOME}/VERSION" | tr -d '[:space:]')
        if [ -n "${file_version}" ]; then
            echo "${file_version}"
            return 0
        fi
    fi
    
    echo "latest"
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
    
    if systemctl is-active --quiet nginx 2>/dev/null; then
        echo "Stopping nginx (container will handle requests directly)..."
        sudo systemctl stop nginx || true
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
}

update_compose_file() {
    local registry=$1
    local version=$2
    
    echo -e "${YELLOW}Updating Docker Compose configuration...${RESET}"
    
    local image_tag="${registry}/${REPO_NAME}:${version}"
    local compose_file
    local mode
    
    if [ "${TEST_MODE}" = true ]; then
        mode="test"
        compose_file="${COMPOSE_TEST}"
    else
        mode="prod"
        compose_file="${COMPOSE_PROD}"
    fi
    
    # Use Python script to generate compose file
    local script_dir=$(dirname "$(readlink -f "$0")")
    local generate_script="${script_dir}/generate-compose.py"
    
    if [ ! -f "${generate_script}" ]; then
        echo -e "${RED}Error: generate-compose.py not found at ${generate_script}${RESET}"
        exit 1
    fi
    
    if ! python3 "${generate_script}" "${mode}" \
        --registry "${registry}" \
        --version "${version}" \
        --emol-home "${EMOL_HOME}" \
        --config-dir "${CONFIG_DIR}" \
        --output "${compose_file}"; then
        echo -e "${RED}Error: Failed to generate compose file${RESET}"
        exit 1
    fi
    
    echo -e "${GREEN}Updated image to: ${image_tag}${RESET}"
}

start_container() {
    local compose_file
    local compose_name
    
    if [ "${TEST_MODE}" = true ]; then
        compose_file="docker-compose.test.yml"
        compose_name="emol_test"
    else
        compose_file="docker-compose.prod.yml"
        compose_name="emol_prod"
    fi
    
    echo -e "${YELLOW}Starting ${compose_name} container...${RESET}"
    cd "${EMOL_HOME}"
    docker-compose -f "${compose_file}" up -d
    
    echo -e "${YELLOW}Waiting for container to be healthy...${RESET}"
    
    # Wait loop for healthcheck
    local max_retries=12  # 12 * 5s = 60s
    local count=0
    
    while [ $count -lt $max_retries ]; do
        sleep 5
        local status=$(docker-compose -f "${compose_file}" ps | grep "${compose_name}" || true)
        
        if echo "$status" | grep -q "healthy"; then
            echo -e "${GREEN}Container started successfully and is healthy${RESET}"
            return 0
        fi
        
        if ! echo "$status" | grep -q "Up"; then
             echo -e "${RED}Container failed to start or exited${RESET}"
             docker-compose -f "${compose_file}" logs
             exit 1
        fi
        
        echo -n "."
        count=$((count + 1))
    done

    echo -e "\n${RED}Timed out waiting for container to be healthy${RESET}"
    docker-compose -f "${compose_file}" logs
    exit 1
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
ACCOUNT_ID=""
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --account)
            ACCOUNT_ID=$2
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

if [ -z "${ACCOUNT_ID}" ]; then
    echo -e "${RED}Error: --account is required${RESET}"
    show_help
fi

REGISTRY=$(build_registry_url "${ACCOUNT_ID}")

load_aws_credentials

if [ -z "${VERSION}" ]; then
    # Determine if we should include beta versions (only in test mode)
    INCLUDE_BETA=false
    if [ "${TEST_MODE}" = true ]; then
        INCLUDE_BETA=true
    fi

    # Try to get version from ECR or VERSION file, default to "latest"
    VERSION=$(get_current_version "${REGISTRY}" "${INCLUDE_BETA}")
    if [ -z "${VERSION}" ] || [ "${VERSION}" = "latest" ]; then
        VERSION="latest"
        echo -e "${GREEN}Using version: ${VERSION}${RESET}"
    else
        echo -e "${GREEN}Using version: ${VERSION}${RESET}"
    fi
fi

# Add 'v' prefix if not "latest" and doesn't already have it
if [ "${VERSION}" != "latest" ] && [[ ! "${VERSION}" =~ ^v ]]; then
    VERSION="v${VERSION}"
fi

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would deploy version: ${VERSION}${RESET}"
    echo -e "${YELLOW}[DRY RUN] Would pull from: ${REGISTRY}/${REPO_NAME}:${VERSION}${RESET}"
    exit 0
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
    echo -e "${YELLOW}Container is running on port 8443${RESET}"
    echo -e "${YELLOW}Existing service is still running on port 80${RESET}"
    echo -e "\n${YELLOW}Note: Running both services uses more resources.${RESET}"
    echo -e "${YELLOW}Monitor with: docker stats && free -h${RESET}"
    echo -e "\nTest the container:"
    echo -e "  https://emol.ealdormere.ca:8443 (via nginx proxy)"
    echo -e "  http://localhost:8080 (direct, for debugging)"
    echo -e "\n${YELLOW}Note: Ensure nginx test proxy is configured and port 8443 is open in firewall${RESET}"
    echo -e "\nWhen ready to cutover, run:"
    echo -e "  $0 --account ${ACCOUNT_ID} --cutover"
    echo -e "\nTo stop old service and save resources:"
    echo -e "  sudo systemctl stop emol nginx"
elif [ "${CUTOVER_MODE}" = true ]; then
    echo -e "\n${GREEN}Cutover complete! Container is now running on port 8000${RESET}"
    echo -e "${YELLOW}Old service and nginx have been stopped${RESET}"
    echo -e "\n${YELLOW}Next steps:${RESET}"
    echo -e "  1. Configure nginx to proxy to the container:"
    echo -e "     sudo cp ${EMOL_HOME}/setup_files/configs/nginx/prod-proxy.conf /etc/nginx/sites-available/emol-prod"
    echo -e "     sudo ln -s /etc/nginx/sites-available/emol-prod /etc/nginx/sites-enabled/"
    echo -e "     sudo nginx -t && sudo systemctl reload nginx"
    echo -e "  2. Verify the container is working correctly"
    echo -e "  3. Archive the old installation at /opt/emol (if desired)"
    echo -e "  4. Update any monitoring/backup scripts to use ${EMOL_HOME}"
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

