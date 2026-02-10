#!/bin/bash

# Docker Build Script for ecommerce-frontend
# This script builds the Docker image with proper tagging and versioning

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-ecommerce-frontend}"
REGISTRY="${REGISTRY:-}"
VERSION="${VERSION:-latest}"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Environment variables with defaults
REACT_APP_API_URL="${REACT_APP_API_URL:-http://localhost:8000/api}"
REACT_APP_ENV="${REACT_APP_ENV:-production}"

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$BLUE" "  $1"
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Parse command line arguments
NO_CACHE=false
PUSH=false
LATEST=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-latest)
            LATEST=false
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --api-url)
            REACT_APP_API_URL="$2"
            shift 2
            ;;
        --env)
            REACT_APP_ENV="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-cache          Build without using cache"
            echo "  --push              Push image to registry after building"
            echo "  --no-latest         Don't tag as 'latest'"
            echo "  --version VERSION   Specify version tag (default: latest)"
            echo "  --registry REGISTRY Specify Docker registry"
            echo "  --api-url URL       Set REACT_APP_API_URL"
            echo "  --env ENV           Set REACT_APP_ENV (development|production)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  IMAGE_NAME          Image name (default: ecommerce-frontend)"
            echo "  REGISTRY            Docker registry URL"
            echo "  VERSION             Image version tag"
            echo "  REACT_APP_API_URL   Backend API URL"
            echo "  REACT_APP_ENV       Environment name"
            echo ""
            echo "Examples:"
            echo "  $0 --version v1.0.0 --push"
            echo "  $0 --no-cache --api-url https://api.prod.com"
            echo "  REGISTRY=myregistry.com $0 --version v2.0.0 --push"
            exit 0
            ;;
        *)
            print_message "$RED" "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Build full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

# Print build configuration
print_header "Docker Build Configuration"
print_message "$GREEN" "Image Name:        ${FULL_IMAGE_NAME}"
print_message "$GREEN" "Version:           ${VERSION}"
print_message "$GREEN" "Git Commit:        ${GIT_COMMIT}"
print_message "$GREEN" "Git Branch:        ${GIT_BRANCH}"
print_message "$GREEN" "Build Date:        ${BUILD_DATE}"
print_message "$GREEN" "API URL:           ${REACT_APP_API_URL}"
print_message "$GREEN" "Environment:       ${REACT_APP_ENV}"
print_message "$GREEN" "Use Cache:         $([ "$NO_CACHE" = true ] && echo "No" || echo "Yes")"
print_message "$GREEN" "Push to Registry:  $([ "$PUSH" = true ] && echo "Yes" || echo "No")"
print_message "$GREEN" "Tag as Latest:     $([ "$LATEST" = true ] && echo "Yes" || echo "No")"

# Verify Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    print_message "$RED" "Error: Dockerfile not found in current directory"
    exit 1
fi

# Build Docker image
print_header "Building Docker Image"

BUILD_ARGS=(
    --build-arg "REACT_APP_API_URL=${REACT_APP_API_URL}"
    --build-arg "REACT_APP_ENV=${REACT_APP_ENV}"
    --label "org.opencontainers.image.created=${BUILD_DATE}"
    --label "org.opencontainers.image.version=${VERSION}"
    --label "org.opencontainers.image.revision=${GIT_COMMIT}"
    --label "org.opencontainers.image.source=https://github.com/yourorg/ecommerce-frontend"
    -t "${FULL_IMAGE_NAME}:${VERSION}"
)

# Add latest tag if requested
if [ "$LATEST" = true ]; then
    BUILD_ARGS+=(-t "${FULL_IMAGE_NAME}:latest")
fi

# Add no-cache flag if requested
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS+=(--no-cache)
fi

# Add git branch tag if not main/master
if [ "$GIT_BRANCH" != "main" ] && [ "$GIT_BRANCH" != "master" ] && [ "$GIT_BRANCH" != "unknown" ]; then
    SAFE_BRANCH=$(echo "$GIT_BRANCH" | sed 's/[^a-zA-Z0-9._-]/-/g')
    BUILD_ARGS+=(-t "${FULL_IMAGE_NAME}:${SAFE_BRANCH}")
fi

# Execute build
print_message "$YELLOW" "Running: docker build ${BUILD_ARGS[*]} ."
if docker build "${BUILD_ARGS[@]}" .; then
    print_message "$GREEN" "✓ Build successful!"
else
    print_message "$RED" "✗ Build failed!"
    exit 1
fi

# Show image size
print_header "Image Information"
docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Push to registry if requested
if [ "$PUSH" = true ]; then
    print_header "Pushing to Registry"

    if [ -z "$REGISTRY" ]; then
        print_message "$RED" "Error: Registry not specified. Use --registry or set REGISTRY environment variable"
        exit 1
    fi

    print_message "$YELLOW" "Pushing ${FULL_IMAGE_NAME}:${VERSION}"
    if docker push "${FULL_IMAGE_NAME}:${VERSION}"; then
        print_message "$GREEN" "✓ Push successful!"
    else
        print_message "$RED" "✗ Push failed!"
        exit 1
    fi

    # Push latest tag if it exists
    if [ "$LATEST" = true ]; then
        print_message "$YELLOW" "Pushing ${FULL_IMAGE_NAME}:latest"
        if docker push "${FULL_IMAGE_NAME}:latest"; then
            print_message "$GREEN" "✓ Latest tag push successful!"
        else
            print_message "$RED" "✗ Latest tag push failed!"
            exit 1
        fi
    fi
fi

# Print summary
print_header "Build Complete"
print_message "$GREEN" "Successfully built: ${FULL_IMAGE_NAME}:${VERSION}"
if [ "$LATEST" = true ]; then
    print_message "$GREEN" "Also tagged as:     ${FULL_IMAGE_NAME}:latest"
fi

echo ""
print_message "$BLUE" "Next steps:"
echo "  • Test locally:  docker run -p 80:80 ${FULL_IMAGE_NAME}:${VERSION}"
echo "  • View logs:     docker logs -f <container-id>"
echo "  • Inspect:       docker inspect ${FULL_IMAGE_NAME}:${VERSION}"
if [ "$PUSH" = false ]; then
    echo "  • Push image:    docker push ${FULL_IMAGE_NAME}:${VERSION}"
fi
echo ""
