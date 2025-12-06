#!/bin/bash

set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

REPO_NAME="emol"
REGION="ca-central-1"
DOCKERFILE="Dockerfile.container"

show_help() {
    cat << EOF
eMoL Container Build and Push Script

Builds the production container image and pushes it to ECR.

Usage: $0 [options]

Options:
    --registry REGISTRY    ECR registry URL (e.g., 123456789012.dkr.ecr.ca-central-1.amazonaws.com)
    --account-id ID        AWS account ID (will construct registry URL)
    --version VERSION      Specific version to tag (default: from VERSION file)
    --no-push             Build only, don't push to ECR
    --dry-run             Show what would be done without building
    --help                Show this help message

Examples:
    $0 --account-id 123456789012
    $0 --registry 123456789012.dkr.ecr.ca-central-1.amazonaws.com
    $0 --account-id 123456789012 --version v0.2.0
    $0 --account-id 123456789012 --no-push
EOF
    exit 0
}

get_current_version() {
    if [ -f "VERSION" ]; then
        cat VERSION
    else
        echo "0.0.0"
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
REGISTRY=""
ACCOUNT_ID=""
VERSION=""

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
fi

VERSION="v${VERSION}"

if [ -n "${ACCOUNT_ID}" ]; then
    REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
fi

if [ "${DRY_RUN}" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would build: ${REPO_NAME}:${VERSION}${RESET}"
    if [ "${NO_PUSH}" = false ] && [ -n "${REGISTRY}" ]; then
        echo -e "${YELLOW}[DRY RUN] Would push to: ${REGISTRY}/${REPO_NAME}:${VERSION}${RESET}"
    fi
    exit 0
fi

if [ -z "${REGISTRY}" ] && [ "${NO_PUSH}" = false ]; then
    echo -e "${RED}Error: --registry or --account-id is required (or use --no-push)${RESET}"
    show_help
fi

build_image ${VERSION}

if [ "${NO_PUSH}" = false ] && [ -n "${REGISTRY}" ]; then
    check_aws_cli
    ensure_ecr_repo ${REGISTRY}
    login_to_ecr ${REGISTRY}
    push_image ${REGISTRY} ${VERSION}
    
    echo -e "\n${GREEN}Build and push complete!${RESET}"
    echo -e "\nTo deploy on Lightsail instance:"
    echo -e "  ./setup_files/deploy-docker.sh --registry ${REGISTRY}"
else
    echo -e "\n${GREEN}Build complete!${RESET}"
    echo -e "Image: ${REPO_NAME}:${VERSION}"
    echo -e "To push later, run:"
    echo -e "  $0 --registry ${REGISTRY:-<registry-url>}"
fi

