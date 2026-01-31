#!/bin/bash
# Build wheels for multiple Python versions inside manylinux Docker container
# This script is copied into the Docker image and runs during container build

set -e

WHEELS_DIR="/wheels"
BUILD_DIR="/build"
DIST_DIR="${BUILD_DIR}/dist"

mkdir -p "$WHEELS_DIR" "$DIST_DIR"

echo "=== Building wheels for Python 3.9-3.14 ==="
echo

for PYBIN in /opt/python/cp39-cp39 /opt/python/cp310-cp310 /opt/python/cp311-cp311 /opt/python/cp312-cp312 /opt/python/cp313-cp313 /opt/python/cp314-cp314; do
    if [ ! -d "$PYBIN" ]; then
        echo "⚠ Skipping $PYBIN (not available)"
        continue
    fi
    
    PYVER=$(basename "$PYBIN" | sed 's/cp//' | sed 's/-.*//')
    PYMAJOR=${PYVER:0:1}
    PYMINOR=${PYVER:1:2}
    PYTHON_VERSION="${PYMAJOR}.${PYMINOR}"
    
    echo "=== Building for Python ${PYTHON_VERSION} (${PYBIN}) ==="
    
    # Upgrade pip and install build tools
    echo "→ Installing build dependencies..."
    $PYBIN/bin/python -m pip install -q --upgrade pip setuptools wheel build pybind11 cmake numpy setuptools-scm
    
    # Clean previous builds
    echo "→ Cleaning previous builds..."
    cd "$BUILD_DIR"
    rm -rf build dist *.egg-info
    
    # Build wheel
    echo "→ Building wheel..."
    if $PYBIN/bin/python setup.py bdist_wheel 2>&1 | grep -E "Successfully|error|Error" || true; then
        # Find the built wheel
        WHEEL=$(find "$BUILD_DIR/dist" -name "*.whl" -type f 2>/dev/null | head -1)
        
        if [ -n "$WHEEL" ]; then
            echo "→ Repairing wheel for manylinux compatibility..."
            # auditwheel is already available in the manylinux image
            auditwheel repair "$WHEEL" -w "$WHEELS_DIR/" 2>&1 | grep -E "repaired|already compliant|warning" || true
            echo "✓ Wheel processed for Python ${PYTHON_VERSION}"
        else
            echo "⚠ No wheel found after build for Python ${PYTHON_VERSION}"
        fi
    else
        echo "✗ Build failed for Python ${PYTHON_VERSION}"
    fi
    
    # Clean up
    rm -rf "$BUILD_DIR/build" "$BUILD_DIR/dist" "$BUILD_DIR"/*.egg-info
done

# Copy final wheels to dist
echo
echo "=== Finalizing wheels ==="
echo "→ Copying wheels to dist/..."

if [ -d "$WHEELS_DIR" ] && [ -n "$(ls -A $WHEELS_DIR/*.whl 2>/dev/null)" ]; then
    cp "$WHEELS_DIR"/*.whl "$DIST_DIR/" 2>/dev/null || true
    echo "✓ Wheels copied to dist/"
    echo
    echo "=== Final wheels ==="
    ls -lh "$DIST_DIR"/*.whl 2>/dev/null || echo "No wheels found"
else
    echo "⚠ No wheels found in $WHEELS_DIR"
fi

echo
echo "✓ Wheel build complete"
