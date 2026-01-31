#!/bin/bash
# Full Debian package build script for systems with debhelper
set -e

echo "Building Debian package with system tools..."

# Check if we have the necessary tools
if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
    echo "Error: dpkg-buildpackage not found. Install with:"
    echo "  sudo apt-get install build-essential devscripts debhelper"
    exit 1
fi

# Ensure we have uv or pip
if ! command -v uv >/dev/null 2>&1; then
    echo "Warning: uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Get current version
CURRENT_VERSION=$(uvx dunamai from any --no-metadata --style semver)
TIMESTAMP=$(date -R)

echo "Building version: $CURRENT_VERSION"

# Update pyproject.toml version
python3 -c "
import toml
data = toml.load('pyproject.toml')
data['project']['version'] = '$CURRENT_VERSION'
with open('pyproject.toml', 'w') as f:
    toml.dump(data, f)
print(f'Updated pyproject.toml version to {data[\"project\"][\"version\"]}')
"

# Update debian changelog
cat > debian/changelog << EOF
ekfsm ($CURRENT_VERSION-1) stable; urgency=medium

  * Release version $CURRENT_VERSION
  * Automated build from development environment
  * Single-artifact deployment with bundled dependencies
  * High compression packaging for minimal size

 -- Jan Jansen <jan@ekf.de>  $TIMESTAMP
EOF

echo "Updated debian/changelog"

# Clean previous builds
rm -rf debian/ekfsm/ || true
rm -f ../ekfsm_*.deb ../ekfsm_*.changes ../ekfsm_*.buildinfo || true

# Build the package
echo "Building package..."
dpkg-buildpackage -us -uc -b

# Move artifacts
mkdir -p dist
mv ../ekfsm_*.deb dist/
mv ../ekfsm_*.changes dist/ || true
mv ../ekfsm_*.buildinfo dist/ || true

echo ""
echo "✅ Debian package built successfully!"
echo ""
echo "Package information:"
ls -la dist/
echo ""
dpkg-deb -I dist/ekfsm_*.deb
echo ""
echo "Package size:"
du -h dist/ekfsm_*.deb
echo ""
echo "Installation command:"
echo "  sudo dpkg -i dist/ekfsm_${CURRENT_VERSION}-1_all.deb"
