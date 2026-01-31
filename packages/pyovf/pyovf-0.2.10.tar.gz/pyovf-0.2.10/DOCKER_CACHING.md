# Docker Image Persistence & Caching

## Problem Solved ✅

Your Docker image now:

1. **Persists** - Only built once, reused for subsequent builds
2. **Caches layers** - Only rebuilds if Dockerfile or source code changes
3. **Fast rebuilds** - Subsequent builds take ~2-3 minutes instead of 5-10 minutes

## How It Works

### First Build (Full Build)

```bash
bash docker-build-wheels.sh
# Takes: ~5-10 minutes (downloads base image, installs tools, builds wheels)
```

**Steps:**

1. Downloads `quay.io/pypa/manylinux_2_28_x86_64:latest` (~500 MB)
2. Installs cmake, git
3. Builds wheels for Python 3.9-3.14
4. Repairs wheels with auditwheel (adds manylinux tags)
5. Exports image

### Subsequent Builds (Cached)

```bash
bash docker-build-wheels.sh
# Takes: ~2-3 minutes (uses cached layers, just rebuilds your code)
```

**Cached layers:**

- ✓ Base image (manylinux)
- ✓ Build tools (cmake, git)
- ✓ All cached until Dockerfile changes

## Managing Docker Images

### List Images

```bash
docker images | grep pyovf
# Shows: pyovf-builder:latest
```

### Check Image Size

```bash
docker images pyovf-builder:latest --format "table {{.Repository}}\t{{.Size}}"
# ~2.5 GB (normal for manylinux with build tools)
```

### Remove Image (if needed)

```bash
docker rmi pyovf-builder:latest
# Next build will rebuild from scratch
```

### Clean Unused Docker Data

```bash
# Remove dangling images (old versions)
docker image prune -f

# Remove all unused images (careful!)
docker image prune -a -f

# Check total Docker disk usage
docker system df
```

## Rebuilding Scenarios

### Scenario 1: Update Source Code (Normal Case)

```bash
# Edit pyovf source files
nano pyovf/__init__.py

# Rebuild wheels (uses cached image)
bash docker-build-wheels.sh
# Time: ~2-3 minutes ✓ FAST
```

### Scenario 2: Update Dockerfile

```bash
# Edit Dockerfile to change base image or tools
nano Dockerfile

# Rebuild image (rebuilds all layers)
bash docker-build-wheels.sh
# Time: ~5-10 minutes (rebuilds everything)
```

### Scenario 3: Force Clean Rebuild

```bash
# Remove old image
docker rmi pyovf-builder:latest

# Rebuild from scratch
bash docker-build-wheels.sh
# Time: ~5-10 minutes (same as first build)
```

## Docker Build Cache Layers

The Dockerfile is organized to maximize cache efficiency:

```dockerfile
FROM quay.io/pypa/manylinux_2_28_x86_64:latest
↓ (Cached - rarely changes)

RUN yum install cmake git
↓ (Cached - only if changed)

COPY . /build/
↓ (Invalidates if any source changes)

RUN [build wheels for Python 3.9-3.14]
↓ (Runs when source changes)

Result: dist/*.whl with manylinux tags ✓
```

## Performance Timeline

### First Build

```txt
Download base image:     ~1-2 min
Install tools:           ~30 sec
Build wheels (6 ver):    ~3-4 min
Total:                   ~5-10 min
```

### Subsequent Builds

```txt
Check cache:             ~5 sec
Rebuild wheels only:     ~2-3 min
Total:                   ~2-3 min  ← 3x faster! ✓
```

## Integration with local-ci.sh

The `build-docker` command in `local-ci.sh` automatically handles persistence:

```bash
# First time (builds image)
bash local-ci.sh build-docker
# Time: ~5-10 min

# Second time (uses cached image)
bash local-ci.sh build-docker
# Time: ~2-3 min ← Much faster!

# Third time (same as second)
bash local-ci.sh build-docker
# Time: ~2-3 min ← Still fast!
```

## Disk Space Management

### Docker Storage Location

- **Linux**: `/var/lib/docker/` (~2.5 GB per image)
- **macOS**: `~/Library/Containers/com.docker.docker/` (~2.5 GB per image)
- **Windows**: `C:\ProgramData\Docker\` (~2.5 GB per image)

### Free Up Space

```bash
# Clean up unused images (safe)
docker system prune

# Remove specific image
docker rmi pyovf-builder:latest

# Aggressive cleanup (removes all unused containers/images)
docker system prune -a
```

## Workflow Optimization

### Best Practice

```bash
# 1. Make code changes
git add .
git commit -m "Update pyovf code"

# 2. Rebuild wheels (fast - uses cache)
bash local-ci.sh build-docker

# 3. Test wheels
bash local-ci.sh test

# 4. Deploy
bash local-ci.sh deploy
```

### Full Deployment Pipeline

```bash
# Tag release
bash local-ci.sh create-tag

# Build wheels (2-3 minutes thanks to cache)
bash local-ci.sh build-docker

# Test wheels
bash local-ci.sh test

# Deploy to PyPI
export PYPI_TOKEN="pypi-..."
bash local-ci.sh deploy

# Done! Total time: ~10-15 minutes for full pipeline
```

## Troubleshooting

### Docker Image Takes Too Long

**Solution**: It's using cache. Just wait, or run:

```bash
docker system df
# Shows current usage
```

### Wheels Not in dist/ After Build

**Solution**: Check if Docker container was successful:

```bash
docker run --rm -v $(pwd):/build pyovf-builder:latest ls -lh /build/dist/
```

### Image Out of Sync with Source

**Solution**: Force rebuild:

```bash
docker rmi -f pyovf-builder:latest
bash docker-build-wheels.sh
```

### Docker Disk Usage Too High

**Solution**: Clean unused images:

```bash
docker system prune -a -f
# Removes unused images and frees ~2.5 GB
```

## Benefits Summary

| Feature | Before | After |
| ------- | ------ | ----- |
| First build | N/A | ~5-10 min |
| Subsequent builds | N/A | ~2-3 min |
| Code changes rebuild | N/A | 3x faster ✓ |
| Disk per image | N/A | ~2.5 GB |
| PyPI compatible wheels | ❌ linux_x86_64 | ✅ manylinux_2_28 |

## Next Steps

1. **First build**: `bash docker-build-wheels.sh` (5-10 min)
2. **Check wheels**: `ls -lh dist/*.whl` (should have manylinux tags)
3. **Deploy**: `bash local-ci.sh deploy`
4. **Future builds**: Just run the command again (~2-3 min) ✓

The Docker image is now persistent and will be reused automatically!
