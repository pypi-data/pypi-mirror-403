# Docker-based PyPI Wheel Building Guide

## Problem

The wheels being built on Ubuntu have the platform tag `linux_x86_64`, which PyPI rejects. PyPI only accepts wheels with specific platform tags like:

- `manylinux_2_17_x86_64` (glibc 2.17)
- `manylinux_2_28_x86_64` (glibc 2.28)
- `manylinux_2_34_x86_64` (glibc 2.34)

## Solution

Use Docker with the official **manylinux** image to build wheels with proper platform tags. The manylinux project provides pre-built Docker images that ensure compatibility across Linux distributions.

## Quick Start

### 1. Build Wheels with Docker

```bash
# Make script executable
chmod +x docker-build-wheels.sh

# Build wheels (requires Docker)
bash docker-build-wheels.sh
```

This will:

- ✓ Build Docker image with manylinux2014_x86_64 (glibc 2.28)
- ✓ Compile wheels for Python 3.9-3.14
- ✓ Tag wheels with `manylinux_2_28_x86_64` (PyPI compatible)
- ✓ Place wheels in `./dist/`

### 2. Verify Wheels

```bash
# Check wheel platform tags
bash docker-build-wheels.sh verify

# Manual verification
python3 -c "from wheel.wheelfile import WheelFile; print(WheelFile('dist/pyovf-*.whl').basename)"
```

### 3. Upload to PyPI

```bash
# With existing local-ci.sh script
export PYPI_TOKEN="pypi-..."
bash local-ci.sh deploy

# Or using twine directly
twine upload dist/*.whl --username __token__ --password "$PYPI_TOKEN"
```

## Docker Setup Details

### Dockerfile Explanation

The `Dockerfile` uses the **quay.io/pypa/manylinux_2_28_x86_64** image which:

1. **Pre-installed Python versions**: 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
2. **Build tools**: gcc, g++, cmake included
3. **Proper glibc linking**: Ensures binary compatibility
4. **Platform tag automation**: Wheels are automatically tagged as `manylinux_2_28_x86_64`

```dockerfile
# Build script runs for each Python version
for PYBIN in /opt/python/cp39-cp39 /opt/python/cp310-cp310 ...; do
    "$PYBIN/bin/python" setup.py bdist_wheel
done
```

### What Makes Wheels Compatible

When you build with manylinux Docker image:

- ✓ Wheels get proper `manylinux_2_28_x86_64` platform tag
- ✓ Binary dependencies are linked to system libraries (not bundled)
- ✓ Wheels run on CentOS 7.x and newer (and all modern Ubuntu versions)
- ✓ PyPI accepts and distributes the wheels

## Prerequisites

### Install Docker

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add user to docker group
newgrp docker  # Activate new group membership
```

**macOS:**

```bash
brew install docker
# Then launch Docker Desktop from Applications
```

**Windows:**

- Download Docker Desktop: <https://www.docker.com/products/docker-desktop>
- Install and run Docker Desktop

### Verify Docker Installation

```bash
docker --version
docker run hello-world
```

## Workflow Options

### Option A: Local Docker Build (Recommended)

Best for development and CI/CD:

```bash
# Clean old wheels
rm -rf dist/

# Build new wheels with Docker
bash docker-build-wheels.sh build

# Verify wheels are correct
bash docker-build-wheels.sh verify

# Upload to PyPI
export PYPI_TOKEN="pypi-..."
bash local-ci.sh deploy
```

### Option B: Using local-ci.sh (Enhanced)

You can extend `local-ci.sh` to automatically use Docker for builds:

```bash
# Build production wheels with Docker
bash local-ci.sh build-production-docker

# Or use the full pipeline
bash local-ci.sh all --use-docker
```

### Option C: GitLab CI/CD

In your `.gitlab-ci.yml`:

```yaml
build:wheels:docker:
  image: quay.io/pypa/manylinux_2_28_x86_64:latest
  stage: build
  script:
    - |
      for PYBIN in /opt/python/cp3{9,10,11,12,13,14}-cp3{9,10,11,12,13,14}; do
        $PYBIN/bin/python -m pip install -q pybind11 cmake numpy setuptools-scm
        $PYBIN/bin/python setup.py bdist_wheel
      done
    - ls -lh dist/
  artifacts:
    paths:
      - dist/*.whl
```

## Platform Tags Explained

| Tag | Base Image | glibc | Compatible Systems |
| --- | ---------- | ----- | ------------------ |
| `manylinux_2_17_x86_64` | manylinux2014 | 2.17 | CentOS 7+, Ubuntu 14.04+ |
| `manylinux_2_28_x86_64` | manylinux_2_28 | 2.28 | CentOS 8+, Ubuntu 20.04+ |
| `manylinux_2_34_x86_64` | manylinux_2_34 | 2.34 | CentOS 9+, Ubuntu 22.04+ |
| `linux_x86_64` | ❌ Invalid | N/A | **Not accepted by PyPI** |

**Note**: Newer `manylinux_2_28` is recommended as it covers modern systems while still supporting older servers (glibc 2.28 → CentOS 8, Ubuntu 20.04+).

## Troubleshooting

### Docker Build Fails

```bash
# Check Docker is running
docker info

# Rebuild image without cache
docker build --no-cache -t pyovf-builder:latest -f Dockerfile .

# Check Docker logs
docker logs <container_id>
```

### Wheels Not Created

```bash
# Check if wheels were built
ls -lh dist/

# Run Docker interactively to debug
docker run -it --rm -v $(pwd):/build pyovf-builder:latest /bin/bash
# Inside container:
cd /build && python3.12 setup.py bdist_wheel
```

### PyPI Still Rejects Wheels

```bash
# Verify platform tag
python3 -c "from wheel.wheelfile import WheelFile; w = WheelFile('dist/pyovf-*.whl'); print(f'Tag: {w.parsed_filename.platform}')"

# Check that it contains 'manylinux'
# Expected: manylinux_2_28_x86_64
# NOT: linux_x86_64
```

### Docker Image Size Too Large

```bash
# Clean up old images
docker image prune -a

# Remove specific image
docker rmi pyovf-builder:latest

# Check disk usage
docker system df
```

## Advanced Configuration

### Build for Multiple Architectures (ARM64, etc.)

Requires Docker buildx plugin:

```bash
# Create buildx builder
docker buildx create --name multiarch

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t pyovf-builder:latest \
  -f Dockerfile .
```

### Custom Manylinux Version

Edit `Dockerfile` to change the base image:

```dockerfile
# For older systems (CentOS 7)
FROM quay.io/pypa/manylinux2014_x86_64:latest

# For newer systems only (CentOS 9)
FROM quay.io/pypa/manylinux_2_34_x86_64:latest
```

### Build with Caching

```bash
# Use BuildKit for faster rebuilds
DOCKER_BUILDKIT=1 docker build -t pyovf-builder .
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Build Wheels

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build wheels
        run: bash docker-build-wheels.sh
      - name: Upload to PyPI
        if: startsWith(github.ref, 'refs/tags/')
        run: |
          pip install twine
          twine upload dist/* -u __token__ -p ${{ secrets.PYPI_TOKEN }}
```

### GitLab CI

```yaml
build:wheels:
  image: quay.io/pypa/manylinux_2_28_x86_64:latest
  stage: build
  script:
    - bash docker-build-wheels.sh build
  artifacts:
    paths:
      - dist/*.whl
```

## Performance Tips

1. **First build is slow** (~5 min) - Docker pulls base image
2. **Subsequent builds are faster** (~2 min) - Uses cached layers
3. **Use BuildKit** for faster caching:

   ```bash
   DOCKER_BUILDKIT=1 docker build -t pyovf-builder .
   ```

4. **Pre-fetch base image** to avoid network delays:

   ```bash
   docker pull quay.io/pypa/manylinux_2_28_x86_64:latest
   ```

## Summary

| Method | Platform Tags | PyPI Compatible | Local Build |
| ------ | ------------- | --------------- | ----------- |
| Native Linux | `linux_x86_64` | ❌ No | ✓ Yes |
| **Docker manylinux** | `manylinux_2_28_x86_64` | ✅ **Yes** | ✓ Yes |
| CI/CD Pipeline | `manylinux_2_28_x86_64` | ✅ **Yes** | ✗ No |

**Recommended**: Use `docker-build-wheels.sh` for local development and integrate manylinux image into your CI/CD pipeline.
