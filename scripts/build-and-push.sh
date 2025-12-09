#!/bin/bash

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

REPO_NAME="emol"
REGION="ca-central-1"
DOCKERFILE="Dockerfile.prod"

show_help() {
    cat << EOF
eMoL Container Build and Push Script

Builds the production container image and pushes to ECR, or deploys directly via SSH.

Usage: $0 [options]

Options:
    --registry REGISTRY    ECR registry URL (e.g., 123456789012.dkr.ecr.ca-central-1.amazonaws.com)
    --account-id ID        AWS account ID (will construct registry URL)
    --version VERSION      Specific version to tag (overrides auto-detection)
    --no-push             Build only, don't push to ECR
    --dry-run             Show what would be done without building
    --ssh-deploy          Deploy directly to Lightsail via SSH (bypasses ECR, for testing)
    --ssh-host HOST       SSH host (e.g., ubuntu@1.2.3.4) - required with --ssh-deploy
    --ssh-key PATH        Path to SSH private key (optional, uses default)
    --remote-path PATH    Remote path on server (default: /home/ubuntu/emol)
    --help                Show this help message

Examples:
    # ECR deployment (production)
    $0 --account-id 123456789012
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com
    
    # Direct SSH deployment (testing/fast iteration)
    $0 --ssh-deploy --ssh-host ubuntu@1.2.3.4
    $0 --ssh-deploy --ssh-host ubuntu@1.2.3.4 --ssh-key ~/.ssh/lightsail_key
EOF
    exit 0
}

get_latest_git_tag() {
    # Get the latest git tag, sorted by version (excluding beta tags)
    local latest_tag=$(git tag -l | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | sed 's/^v//' | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)
    
    if [ -z "${latest_tag}" ]; then
        echo "0.0.0"
    else
        echo "${latest_tag}"
    fi
}

get_latest_beta_tag() {
    local base_version=$1
    # Get the latest beta tag for this base version
    local latest_beta=$(git tag -l | grep -E "^v?${base_version}-beta\.[0-9]+$" | sed 's/^v//' | sort -t. -k4,4n | tail -1)
    echo "${latest_beta}"
}

get_next_beta_number() {
    local base_version=$1
    local latest_beta=$(get_latest_beta_tag "${base_version}")
    
    if [ -z "${latest_beta}" ]; then
        echo "1"
    else
        # Extract the beta number (e.g., "1.4.0-beta.3" -> "3")
        local beta_num=$(echo "${latest_beta}" | sed -n 's/.*-beta\.\([0-9]\+\)/\1/p')
        if [ -z "${beta_num}" ]; then
            echo "1"
        else
            echo $((beta_num + 1))
        fi
    fi
}

is_feature_branch() {
    local branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if [ -z "${branch}" ]; then
        return 1
    fi
    
    # Check if branch is not main or master
    if [ "${branch}" != "main" ] && [ "${branch}" != "master" ]; then
        return 0
    fi
    return 1
}

get_current_version() {
    local use_beta=false
    
    # Check if we should use beta tagging (feature branch and no explicit version)
    if [ -z "${VERSION}" ] && is_feature_branch; then
        use_beta=true
    fi
    
    if [ "${use_beta}" = true ]; then
        local base_version=$(get_latest_git_tag)
        local beta_num=$(get_next_beta_number "${base_version}")
        local version="${base_version}-beta.${beta_num}"
        
        echo "${version}" > VERSION
        echo "${version}"
    else
        # Get version from git tag and update VERSION file
        local version=$(get_latest_git_tag)
        echo "${version}" > VERSION
        echo "${version}"
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${RESET}"
        exit 1
    fi
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}AWS CLI is not installed${RESET}"
        exit 1
    fi
}

check_ssh() {
    if ! command -v ssh &> /dev/null || ! command -v scp &> /dev/null; then
        echo -e "${RED}SSH/SCP is not installed${RESET}"
        exit 1
    fi
}

deploy_via_ssh() {
    local version=$1
    local ssh_host=$2
    local ssh_key=$3
    local remote_path=$4
    
    local image_name="${REPO_NAME}:${version}"
    local tar_file="/tmp/${REPO_NAME}-${version}.tar"
    local remote_tar="${remote_path}/$(basename ${tar_file})"
    
    echo -e "${YELLOW}Preparing image for SSH transfer...${RESET}"
    
    # Save image to tar file
    echo -e "${YELLOW}Saving image to ${tar_file}...${RESET}"
    docker save ${image_name} -o ${tar_file}
    
    if [ ! -f "${tar_file}" ]; then
        echo -e "${RED}Failed to save image${RESET}"
        exit 1
    fi
    
    local tar_size=$(du -h ${tar_file} | cut -f1)
    echo -e "${GREEN}Image saved: ${tar_size}${RESET}"
    
    # Build SSH command with optional key
    local ssh_cmd="ssh"
    local scp_cmd="scp"
    if [ -n "${ssh_key}" ]; then
        ssh_cmd="${ssh_cmd} -i ${ssh_key}"
        scp_cmd="${scp_cmd} -i ${ssh_key}"
    fi
    
    # Test SSH connection
    echo -e "${YELLOW}Testing SSH connection to ${ssh_host}...${RESET}"
    if ! ${ssh_cmd} -o ConnectTimeout=5 ${ssh_host} "echo 'Connection successful'" &>/dev/null; then
        echo -e "${RED}Failed to connect to ${ssh_host}${RESET}"
        echo -e "${YELLOW}Check:${RESET}"
        echo -e "  1. SSH host is correct"
        echo -e "  2. SSH key is valid (if using --ssh-key)"
        echo -e "  3. Server is accessible"
        rm -f ${tar_file}
        exit 1
    fi
    
    # Transfer tar file
    echo -e "${YELLOW}Transferring image to ${ssh_host}:${remote_tar}...${RESET}"
    ${scp_cmd} ${tar_file} ${ssh_host}:${remote_tar}
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to transfer image${RESET}"
        rm -f ${tar_file}
        exit 1
    fi
    
    echo -e "${GREEN}Image transferred successfully${RESET}"
    
    # Load image on remote server
    echo -e "${YELLOW}Loading image on remote server...${RESET}"
    ${ssh_cmd} ${ssh_host} "cd ${remote_path} && docker load -i ${remote_tar}"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to load image on remote server${RESET}"
        ${ssh_cmd} ${ssh_host} "rm -f ${remote_tar}"
        rm -f ${tar_file}
        exit 1
    fi
    
    # Tag as latest on remote
    ${ssh_cmd} ${ssh_host} "docker tag ${image_name} ${REPO_NAME}:latest"
    
    # Clean up remote tar file
    ${ssh_cmd} ${ssh_host} "rm -f ${remote_tar}"
    
    # Clean up local tar file
    rm -f ${tar_file}
    
    echo -e "${GREEN}Image deployed successfully to ${ssh_host}${RESET}"
    echo -e "  ${image_name}"
    echo -e "  ${REPO_NAME}:latest"
    echo -e "\n${YELLOW}Note: Image is loaded on server but not deployed yet.${RESET}"
    echo -e "${YELLOW}For production, use ECR deployment with deploy-docker.sh${RESET}"
}

login_to_ecr() {
    local registry=$1
    
    echo -e "${YELLOW}Logging in to ECR...${RESET}"
    aws ecr get-login-password --region ${REGION} | \
        docker login --username AWS --password-stdin ${registry}
}

ensure_ecr_repo() {
    local registry=$1
    local account_id=$(echo $registry | cut -d'.' -f1)
    
    echo -e "${YELLOW}Ensuring ECR repository exists...${RESET}"
    if ! aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${REGION} &>/dev/null; then
        echo -e "${YELLOW}Creating ECR repository...${RESET}"
        aws ecr create-repository \
            --repository-name ${REPO_NAME} \
            --region ${REGION} \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        echo -e "${GREEN}ECR repository created${RESET}"
    else
        echo -e "${GREEN}ECR repository already exists${RESET}"
    fi
}

build_image() {
    local version=$1
    
    echo -e "${YELLOW}Building Docker image...${RESET}"
    echo -e "  Dockerfile: ${DOCKERFILE}"
    echo -e "  Tag: ${REPO_NAME}:${version}"
    
    if ! docker build -f ${DOCKERFILE} -t ${REPO_NAME}:${version} .; then
        echo -e "${RED}Build failed!${RESET}"
        echo -e "${YELLOW}Common issues:${RESET}"
        echo -e "  1. Permission denied: Add user to docker group or use sudo"
        echo -e "  2. .cursor directory: Check .dockerignore file"
        echo -e "  3. See DOCKER_BUILD_TROUBLESHOOTING.md for more help"
        exit 1
    fi
    
    docker tag ${REPO_NAME}:${version} ${REPO_NAME}:latest
    
    echo -e "${GREEN}Image built successfully${RESET}"
}

push_image() {
    local registry=$1
    local version=$2
    
    echo -e "${YELLOW}Pushing image to ECR...${RESET}"
    
    docker tag ${REPO_NAME}:${version} ${registry}/${REPO_NAME}:${version}
    docker tag ${REPO_NAME}:latest ${registry}/${REPO_NAME}:latest
    
    docker push ${registry}/${REPO_NAME}:${version}
    docker push ${registry}/${REPO_NAME}:latest
    
    echo -e "${GREEN}Image pushed successfully${RESET}"
    echo -e "  ${registry}/${REPO_NAME}:${version}"
    echo -e "  ${registry}/${REPO_NAME}:latest"
}

DRY_RUN=false
NO_PUSH=false
SSH_DEPLOY=false
REGISTRY=""
ACCOUNT_ID=""
VERSION=""
SSH_HOST=""
SSH_KEY=""
REMOTE_PATH="/home/ubuntu/emol"

while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            REGISTRY=$2
            shift 2
            ;;
        --account-id)
            ACCOUNT_ID=$2
            shift 2
            ;;
        --version)
            VERSION=$2
            shift 2
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --ssh-deploy)
            SSH_DEPLOY=true
            shift
            ;;
        --ssh-host)
            SSH_HOST=$2
            shift 2
            ;;
        --ssh-key)
            SSH_KEY=$2
            shift 2
            ;;
        --remote-path)
            REMOTE_PATH=$2
            shift 2
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

check_docker

if [ -z "${VERSION}" ]; then
    VERSION=$(get_current_version)
    if is_feature_branch; then
        echo -e "${GREEN}Using beta version from feature branch: ${VERSION}${RESET}"
    else
        echo -e "${GREEN}Using latest git tag: ${VERSION}${RESET}"
    fi
else
    # Remove 'v' prefix if present, then write to VERSION file
    VERSION=$(echo "${VERSION}" | sed 's/^v//')
    echo "${VERSION}" > VERSION
    echo -e "${GREEN}Using specified version: ${VERSION}${RESET}"
fi

VERSION="v${VERSION}"

if [ -n "${ACCOUNT_ID}" ]; then
    REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
fi

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would build: ${REPO_NAME}:${VERSION}${RESET}"
    if [ "${SSH_DEPLOY}" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would deploy via SSH to: ${SSH_HOST:-<not specified>}${RESET}"
    elif [ "${NO_PUSH}" = false ] && [ -n "${REGISTRY}" ]; then
        echo -e "${YELLOW}[DRY RUN] Would push to: ${REGISTRY}/${REPO_NAME}:${VERSION}${RESET}"
    fi
    exit 0
fi

# Validate SSH deployment requirements
if [ "${SSH_DEPLOY}" = true ]; then
    if [ -z "${SSH_HOST}" ]; then
        echo -e "${RED}Error: --ssh-host is required when using --ssh-deploy${RESET}"
        show_help
    fi
    if [ -n "${SSH_KEY}" ] && [ ! -f "${SSH_KEY}" ]; then
        echo -e "${RED}Error: SSH key file not found: ${SSH_KEY}${RESET}"
        exit 1
    fi
    check_ssh
fi

# Validate ECR deployment requirements
if [ "${SSH_DEPLOY}" = false ] && [ -z "${REGISTRY}" ] && [ "${NO_PUSH}" = false ]; then
    echo -e "${RED}Error: --registry or --account-id is required (or use --no-push or --ssh-deploy)${RESET}"
    show_help
fi

build_image ${VERSION}

if [ "${SSH_DEPLOY}" = true ]; then
    deploy_via_ssh ${VERSION} "${SSH_HOST}" "${SSH_KEY}" "${REMOTE_PATH}"
elif [ "${NO_PUSH}" = false ] && [ -n "${REGISTRY}" ]; then
    check_aws_cli
    ensure_ecr_repo ${REGISTRY}
    login_to_ecr ${REGISTRY}
    push_image ${REGISTRY} ${VERSION}
    
    echo -e "\n${GREEN}Build and push complete!${RESET}"
    echo -e "\nTo deploy on Lightsail instance:"
    echo -e "  ./setup_files/host/deploy-docker.sh --registry ${REGISTRY}"
else
    echo -e "\n${GREEN}Build complete!${RESET}"
    echo -e "Image: ${REPO_NAME}:${VERSION}"
    echo -e "To push later, run:"
    echo -e "  $0 --registry ${REGISTRY:-<registry-url>}"
fi

