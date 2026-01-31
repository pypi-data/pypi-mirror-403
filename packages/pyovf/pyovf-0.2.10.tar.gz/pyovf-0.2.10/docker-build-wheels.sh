#!/bin/bash
# Docker-based wheel builder for PyPI-compatible manylinux wheels
# This script builds wheels with proper manylinux platform tags
# Usage: bash docker-build-wheels.sh [python-version]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DIST_DIR="${PROJECT_DIR}/dist"
DOCKER_IMAGE="pyovf-builder:latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
log_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

log_stage() {
    echo -e "${CYAN}→${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        echo
        log_stage "Installation instructions:"
        echo "  Ubuntu/Debian: sudo apt-get install docker.io"
        echo "  macOS: brew install docker"
        echo "  Or download from: https://www.docker.com/products/docker-desktop"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        echo
        log_stage "Start Docker:"
        echo "  Ubuntu/Linux: sudo systemctl start docker"
        echo "  macOS: open /Applications/Docker.app"
        return 1
    fi
    
    log_success "Docker is available"
    return 0
}

# Build Docker image
build_docker_image() {
    log_header "BUILDING DOCKER IMAGE"
    
    log_stage "Building manylinux Docker image..."
    
    if docker build \
        -t "$DOCKER_IMAGE" \
        -f "${PROJECT_DIR}/Dockerfile" \
        "${PROJECT_DIR}" 2>&1 | tail -20; then
        log_success "Docker image built: $DOCKER_IMAGE"
        return 0
    else
        log_error "Failed to build Docker image"
        return 1
    fi
}

# Build wheels using Docker
build_wheels_docker() {
    log_header "BUILDING WHEELS IN DOCKER"
    
    # Create dist directory
    mkdir -p "$DIST_DIR"
    
    log_stage "Extracting wheels from Docker image (Python 3.9-3.14)..."
    
    local container_name="pyovf-wheel-build-tmp"
    
    # Create a throwaway container and copy the prebuilt wheels out of the image.
    if docker create --name "$container_name" "$DOCKER_IMAGE" >/dev/null; then
        if docker cp "$container_name:/build/dist/." "$DIST_DIR/"; then
            log_success "Wheels copied to host dist/"
        else
            log_error "Failed to copy wheels from container"
            docker rm -f "$container_name" >/dev/null 2>&1 || true
            return 1
        fi
        docker rm -f "$container_name" >/dev/null 2>&1 || true
    else
        log_error "Failed to create container from image"
        return 1
    fi
    
    # List built wheels
    echo
    log_stage "Built wheels:"
    if ls -lh "$DIST_DIR"/*.whl 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}'; then
        return 0
    else
        log_warning "No wheels found in dist/"
        return 1
    fi
}

# Verify wheel compatibility
verify_wheels() {
    log_header "VERIFYING WHEEL COMPATIBILITY"
    
    log_stage "Checking wheel platform tags..."
    
    local found_valid=0
    local total=0
    
    while IFS= read -r wheel_file; do
        if [ -n "$wheel_file" ]; then
            ((++total))
            local filename
            filename=$(basename "$wheel_file")
            
            # Check if filename contains manylinux (in any position)
            if echo "$filename" | grep -q 'manylinux'; then
                log_success "$filename"
                found_valid=1
            else
                log_warning "$filename (may not be PyPI compatible)"
            fi
        fi
    done < <(find "$DIST_DIR" -maxdepth 1 -type f -name "*.whl" 2>/dev/null)
    
    if [ $total -eq 0 ]; then
        log_warning "No wheels found in dist/"
        return 1
    fi
    
    if [ $found_valid -gt 0 ]; then
        echo
        log_success "Found $found_valid wheel(s) with manylinux tag ✓"
        return 0
    else
        log_warning "No wheels with manylinux tag found"
        return 1
    fi
}

# Clean up
cleanup_docker() {
    log_header "CLEANUP"
    
    read -p "Remove Docker image $DOCKER_IMAGE? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_stage "Removing Docker image..."
        docker rmi -f "$DOCKER_IMAGE" || log_warning "Failed to remove image"
        log_success "Docker image removed"
    fi
}

# Show usage
show_usage() {
    cat << 'EOF'
Docker-based PyPI Wheel Builder

Usage: bash docker-build-wheels.sh [COMMAND]

COMMANDS:
  build           Build wheels using Docker (default)
  verify          Verify existing wheels in dist/
  clean           Clean up Docker image
  help            Show this help message

EXAMPLES:
  bash docker-build-wheels.sh               # Build wheels
  bash docker-build-wheels.sh verify        # Check wheel platform tags
  bash docker-build-wheels.sh clean         # Remove Docker image

REQUIREMENTS:
  - Docker installed and running
  - Internet connection (to download base image)
  - ~2GB disk space for Docker images and wheels

OUTPUT:
  - Wheels are built in: ./dist/
  - Platform tags: manylinux_2_28_x86_64 (glibc 2.28)
  - Architectures: x86_64, aarch64 (with buildx plugin)

INSTALL FROM WHEELS:
  pip install --no-index --find-links ./dist pyovf

UPLOAD TO PyPI:
  export PYPI_TOKEN="pypi-..."
  twine upload dist/

EOF
}

# Main
main() {
    local command="${1:-build}"
    
    case "$command" in
        build)
            log_header "PYPI WHEEL BUILDER (Docker-based)"
            check_docker || exit 1
            build_docker_image || exit 1
            build_wheels_docker || exit 1
            verify_wheels || log_warning "Wheel verification failed"
            echo
            log_header "BUILD COMPLETE"
            echo
            log_stage "Next steps:"
            echo "  1. Verify wheels: ls -lh dist/"
            echo "  2. Install locally: pip install --no-index --find-links ./dist pyovf"
            echo "  3. Upload to PyPI: bash local-ci.sh deploy"
            ;;
        verify)
            verify_wheels
            ;;
        clean)
            cleanup_docker
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
