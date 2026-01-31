#!/bin/bash
# Debian package dependency bundling script with .pth file generation
set -e

PACKAGE_NAME="ekfsm"
INSTALL_DIR="/opt/ekfsm"
VENV_DIR="$INSTALL_DIR/venv"
PTH_DIR="/usr/lib/python3/dist-packages"
PTH_FILE="$PTH_DIR/ekfsm-bundled.pth"

# Determine Python version dynamically
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
SITE_PACKAGES="$VENV_DIR/lib/python$PYTHON_VERSION/site-packages"

echo "Setting up bundled dependencies for $PACKAGE_NAME"
echo "Python version: $PYTHON_VERSION"
echo "Virtual environment: $VENV_DIR"
echo "Site packages: $SITE_PACKAGES"

# Create directories in debian package structure
mkdir -p "debian/tmp$INSTALL_DIR"
mkdir -p "debian/tmp$PTH_DIR"
mkdir -p "debian/tmp/usr/bin"

# Create virtual environment
echo "Creating virtual environment..."
if command -v uv >/dev/null 2>&1; then
    uv venv "debian/tmp$VENV_DIR" --python python3.10
else
    # Fallback for systems without uv
    if python3.10 -c "import venv" 2>/dev/null; then
        python3.10 -m venv "debian/tmp$VENV_DIR"
    elif python3 -c "import venv" 2>/dev/null; then
        python3 -m venv "debian/tmp$VENV_DIR"
    else
        echo "Error: Neither uv nor python venv module available."
        echo "Please install python3-venv package or uv"
        exit 1
    fi
fi

# Determine actual Python version used by the virtual environment
ACTUAL_PYTHON_VERSION=$("debian/tmp$VENV_DIR/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ACTUAL_SITE_PACKAGES="$VENV_DIR/lib/python$ACTUAL_PYTHON_VERSION/site-packages"

echo "Virtual environment created with Python $ACTUAL_PYTHON_VERSION"
echo "Actual site packages: $ACTUAL_SITE_PACKAGES"

# Upgrade pip in the venv
echo "Upgrading pip..."
if command -v uv >/dev/null 2>&1; then
    uv pip install --python "debian/tmp$VENV_DIR/bin/python" --upgrade pip
else
    "debian/tmp$VENV_DIR/bin/pip" install --upgrade pip
fi

# Generate locked requirements if not already present
if [ ! -f requirements.lock ]; then
    echo "Generating locked requirements (excluding system packages)..."
    if command -v uv >/dev/null 2>&1; then
        uv pip compile pyproject.toml --output-file requirements.lock
        # Remove gpiod from requirements as it's provided by system package
        grep -v "^gpiod" requirements.lock > requirements.lock.tmp && mv requirements.lock.tmp requirements.lock || true
    else
        echo "Warning: uv not found, using pip to install from pyproject.toml"
        python3 -m pip install --no-cache-dir build
        python3 -c "
import toml
import subprocess
import sys

# Read pyproject.toml
with open('pyproject.toml', 'r') as f:
    config = toml.load(f)

# Get dependencies, excluding system packages
deps = config['project']['dependencies']
filtered_deps = [dep for dep in deps if not dep.startswith('gpiod')]

# Write filtered requirements.lock
with open('requirements.lock', 'w') as f:
    f.write('# Generated requirements (system packages excluded)\\n')
    for dep in filtered_deps:
        f.write(f'{dep}\\n')
"
    fi
fi

# Install dependencies with locked versions
echo "Installing locked dependencies..."
if command -v uv >/dev/null 2>&1; then
    uv pip install --python "debian/tmp$VENV_DIR/bin/python" --no-cache-dir -r requirements.lock
else
    "debian/tmp$VENV_DIR/bin/pip" install --no-cache-dir -r requirements.lock
fi

# Install the package itself
echo "Installing ekfsm package..."
if command -v uv >/dev/null 2>&1; then
    uv pip install --python "debian/tmp$VENV_DIR/bin/python" --no-cache-dir --no-deps .
else
    "debian/tmp$VENV_DIR/bin/pip" install --no-cache-dir --no-deps .
fi

# Create .pth file for system integration
echo "Creating .pth file..."
cat > "debian/tmp$PTH_FILE" << EOF
# ekfsm bundled dependencies path
# This file allows system Python to find the bundled ekfsm dependencies
/opt/ekfsm/venv/lib/python3.10/site-packages
EOF

# Create optimized wrapper script
echo "Creating wrapper script..."
cat > "debian/tmp/usr/bin/ekfsm-cli" << 'EOF'
#!/bin/bash
# ekfsm CLI wrapper script
# Uses bundled dependencies from /opt/ekfsm/venv

# Primary path for Python 3.10 (our bundled version)
VENV_SITE_PACKAGES="/opt/ekfsm/venv/lib/python3.10/site-packages"
VENV_PYTHON="/opt/ekfsm/venv/bin/python"

# Check if bundled Python exists, otherwise use system python
if [[ -x "$VENV_PYTHON" ]]; then
    PYTHON_CMD="$VENV_PYTHON"
else
    PYTHON_CMD="python3"
fi

# Set up environment
export PYTHONPATH="$VENV_SITE_PACKAGES:$PYTHONPATH"
export PYTHONNOUSERSITE=1  # Prevent user site-packages conflicts

# Execute with appropriate interpreter
exec "$PYTHON_CMD" -c "
import sys
import os

# Add bundled site-packages to path
site_packages = '/opt/ekfsm/venv/lib/python3.10/site-packages'
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.insert(0, site_packages)

from ekfsm.cli import main
main()
" "$@"
EOF

chmod +x "debian/tmp/usr/bin/ekfsm-cli"

# Optimization: Remove unnecessary files to reduce package size
echo "Optimizing package size..."

# Remove tests directory from main package
rm -rf "debian/tmp/tests" 2>/dev/null || true

# Clean up virtual environment
find "debian/tmp$VENV_DIR" -type f -name "*.pyc" -delete
find "debian/tmp$VENV_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -type f -name "*.pyo" -delete
find "debian/tmp$VENV_DIR" -type d -name "test*" -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove documentation and examples to save space
find "debian/tmp$VENV_DIR" -name "doc*" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "example*" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "*.md" -delete 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "*.rst" -delete 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "*.txt" -not -path "*/site-packages/ekfsm*" -delete 2>/dev/null || true

# Remove pip from bundled dependencies (not needed for deployment)
find "debian/tmp$VENV_DIR" -name "pip*" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -name "_pip*" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -path "*/site-packages/pip" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -path "*/site-packages/pip-*" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove gpiod from bundled dependencies (provided by system package)
find "debian/tmp$VENV_DIR" -name "gpiod*" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -path "*/site-packages/gpiod" -type d -exec rm -rf {} + 2>/dev/null || true
find "debian/tmp$VENV_DIR" -path "*/site-packages/gpiod-*" -type d -exec rm -rf {} + 2>/dev/null || true

echo "Optimization completed successfully!"

# Update the .pth file to include the gzip importer
echo "Dependency bundling completed successfully!"
echo "Package structure created in debian/tmp/"
echo "Virtual environment: $VENV_DIR"
echo "Actual Python version: $ACTUAL_PYTHON_VERSION"
echo ".pth file: $PTH_FILE"
