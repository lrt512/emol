#!/bin/bash

# Colors for output
GREEN='\033[1;32m'
RED='\033[1;31m'
RESET='\033[0m'

VERSION_FILE="VERSION"
CURRENT_VERSION=$(cat $VERSION_FILE)

# Semantic versioning regex
SEMVER_REGEX="^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"

bump_version() {
    local version=$1
    local part=$2
    
    IFS='.' read -ra VERSION_PARTS <<< "$version"
    
    case $part in
        major)
            ((VERSION_PARTS[0]++))
            VERSION_PARTS[1]=0
            VERSION_PARTS[2]=0
            ;;
        minor)
            ((VERSION_PARTS[1]++))
            VERSION_PARTS[2]=0
            ;;
        patch)
            ((VERSION_PARTS[2]++))
            ;;
        *)
            echo -e "${RED}Invalid version part: $part${RESET}"
            exit 1
            ;;
    esac
    
    echo "${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.${VERSION_PARTS[2]}"
}

show_help() {
    cat << EOF
Version Bump Script

Usage: $0 <major|minor|patch> [--dry-run]

Arguments:
    major       Bump major version (x.0.0)
    minor       Bump minor version (0.x.0)
    patch       Bump patch version (0.0.x)

Options:
    --dry-run   Show what would be done without making changes

Example:
    $0 patch            # Bump patch version
    $0 minor --dry-run  # Show what minor version bump would do
EOF
    exit 0
}

# Parse arguments
DRY_RUN=false
VERSION_PART=""

while [[ $# -gt 0 ]]; do
    case $1 in
        major|minor|patch)
            VERSION_PART=$1
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

if [ -z "$VERSION_PART" ]; then
    echo -e "${RED}Version part (major|minor|patch) is required${RESET}"
    show_help
fi

# Validate current version
if ! [[ $CURRENT_VERSION =~ $SEMVER_REGEX ]]; then
    echo -e "${RED}Current version $CURRENT_VERSION is not valid semantic versioning${RESET}"
    exit 1
fi

# Calculate new version
NEW_VERSION=$(bump_version $CURRENT_VERSION $VERSION_PART)

if [ "$DRY_RUN" = true ]; then
    echo -e "Would bump version from $CURRENT_VERSION to $NEW_VERSION"
    exit 0
fi

# Update version file
echo $NEW_VERSION > $VERSION_FILE

# Create git tag
git add $VERSION_FILE
git commit -m "Bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"

echo -e "${GREEN}Version bumped from $CURRENT_VERSION to $NEW_VERSION${RESET}"
echo -e "${GREEN}Don't forget to push the tag:${RESET}"
echo -e "  git push origin v$NEW_VERSION" 