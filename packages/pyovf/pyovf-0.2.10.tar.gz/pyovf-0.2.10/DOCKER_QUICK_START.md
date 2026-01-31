# PyPI-Compatible Wheel Building - Quick Start

## Problem Solved ✅

Your wheels had the platform tag `linux_x86_64` which PyPI **rejects**.

**Solution**: Build with Docker using the official manylinux image to get proper platform tags like `manylinux_2_28_x86_64`.

## Quick Start (5 minutes)

### 1. Build PyPI-Compatible Wheels

```bash
cd ~/WORK/ovf-framework/pyovf

# Option A: Using local-ci.sh (recommended)
bash local-ci.sh build-docker

# Option B: Using docker-build-wheels.sh script
bash docker-build-wheels.sh
```

### 2. Check the Wheels

```bash
# List wheels built
ls -lh dist/*.whl

# Check platform tags (should contain "manylinux")
for f in dist/*.whl; do echo $f | grep -o '[^-]*$'; done
```

Expected output:

```txt
pyovf-0.2.8-cp39-cp39-manylinux_2_28_x86_64.whl  ✓ PyPI compatible
pyovf-0.2.8-cp310-cp310-manylinux_2_28_x86_64.whl  ✓ PyPI compatible
...
```

### 3. Upload to PyPI

```bash
# Set your PyPI token
export PYPI_TOKEN="pypi-AgEIcHlwaS5vcmc..."

# Deploy using local-ci.sh
bash local-ci.sh deploy

# Or manually with twine
twine upload dist/*.whl -u __token__ -p "$PYPI_TOKEN"
```

## What Changed

### New Files Created

1. **`Dockerfile`** - Builds manylinux wheels automatically
2. **`docker-build-wheels.sh`** - Standalone Docker build script
3. **`local-ci.sh` (updated)** - New `build-docker` command
4. **`DOCKER_WHEELS_GUIDE.md`** - Comprehensive documentation

### Integration into local-ci.sh

The `local-ci.sh` script now includes Docker support:

```bash
# Build Docker-compatible wheels
bash local-ci.sh build-docker

# Run full pipeline with Docker
bash local-ci.sh prepare
bash local-ci.sh build-docker
bash local-ci.sh test
bash local-ci.sh deploy
```

## Requirements

- **Docker**: Install and running
  - Ubuntu: `sudo apt-get install docker.io && sudo systemctl start docker`
  - macOS: `brew install docker && open /Applications/Docker.app`

## How It Works

```txt
┌─────────────────────────────────────────┐
│   Your project files                    │
└────────────────┬────────────────────────┘
                 │
                 ↓
        ┌────────────────────┐
        │  Docker Container  │
        │  (manylinux image) │
        └────────────────────┘
                 │
        ┌────────▼────────────────────────┐
        │ For each Python version (3.9-14):
        │  - Install dependencies         │
        │  - Build wheel with setup.py    │
        │  - Tag as manylinux_2_28        │
        └─────────────────────────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │  Wheels with proper    │
        │  platform tags ✓       │
        │  (PyPI compatible)     │
        └────────────────────────┘
                 │
                 ↓
        ┌─────────────────────────────────┐
        │ ./dist/                         │
        │ ├── pyovf-0.2.8-cp39-cp39-...   │
        │ ├── pyovf-0.2.8-cp310-cp310-... │
        │ └── ...                         │
        └─────────────────────────────────┘
```

## Verification

Wheels built with Docker will have these platform tags:

| Python | Tag |
| ------|-----|
| 3.9 | `manylinux_2_28_x86_64` ✓ |
| 3.10 | `manylinux_2_28_x86_64` ✓ |
| 3.11 | `manylinux_2_28_x86_64` ✓ |
| 3.12 | `manylinux_2_28_x86_64` ✓ |
| 3.13 | `manylinux_2_28_x86_64` ✓ |
| 3.14 | `manylinux_2_28_x86_64` ✓ |

All marked with ✓ are **PyPI compatible**!

## Full Deployment Workflow

```bash
# 1. Create a git tag
bash local-ci.sh create-tag

# 2. Build PyPI-compatible wheels
bash local-ci.sh build-docker

# 3. Test wheels
bash local-ci.sh test

# 4. Deploy to PyPI
export PYPI_TOKEN="pypi-..."
bash local-ci.sh deploy

# Done! ✓
```

## Alternative: Build Locally (Slow, Not Recommended)

If you don't have Docker:

```bash
# Build native wheels (⚠️ will have linux_x86_64 tag)
bash local-ci.sh build

# Install tools to repair wheels
pip install auditwheel

# Repair wheels for manylinux compatibility
auditwheel repair dist/*.whl -w dist/

# This works but is slower and less reliable
```

## Troubleshooting

### "Docker is not running"

```bash
sudo systemctl start docker  # Linux
open /Applications/Docker.app  # macOS
```

### "Permission denied while trying to connect to Docker daemon"

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Wheels still in dist/ from native build

```bash
# Clean old wheels before building
bash local-ci.sh clean
bash local-ci.sh build-docker
```

## Performance

- First build: ~5-10 minutes (downloads Docker base image)
- Subsequent builds: ~2-3 minutes (uses cached image)
- Wheel size: ~110 KB each (small and efficient)

## Platform Compatibility

Wheels built with `manylinux_2_28_x86_64` work on:

- ✅ Ubuntu 20.04 LTS and newer
- ✅ CentOS 8 and newer
- ✅ Debian 11 and newer
- ✅ All modern Linux distributions

## Next Steps

1. Install Docker if needed
2. Run: `bash local-ci.sh build-docker`
3. Verify: `ls -lh dist/*.whl`
4. Deploy: `bash local-ci.sh deploy`

**Questions?** See `DOCKER_WHEELS_GUIDE.md` for comprehensive documentation.
