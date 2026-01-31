# Debian Package Deployment

This document describes the single-artifact Debian package deployment setup for ekfsm.

## Overview

The ekfsm project now supports building deployment-ready Debian packages that include:

- **Single-artifact deployment**: Everything needed is bundled in one .deb file
- **Locked dependencies**: All dependencies are pinned to specific versions for reproducibility
- **High compression**: Package size is minimized through aggressive optimization
- **Ubuntu 22.04 base**: Built and tested on Ubuntu 22.04 LTS
- **Virtual environment isolation**: Dependencies are bundled in a separate virtual environment
- **System integration**: Uses .pth files to integrate with system Python

## Package Structure

```
/opt/ekfsm/
├── venv/                                    # Isolated virtual environment
│   ├── bin/python                          # Python interpreter
│   └── lib/python3.X/site-packages/        # Bundled dependencies
│       ├── ekfsm/                          # Main package
│       ├── gzip_importer.py                # Custom importer for compressed files
│       └── ...                             # All dependencies (compressed)
/usr/bin/ekfsm-cli                          # Main executable wrapper
/usr/local/bin/ekfsm                        # Convenience symlink
/usr/lib/python3/dist-packages/ekfsm-bundled.pth  # Python path configuration
```

## Build Process

### Local Development Build

```bash
# Using devenv
direnv exec . build-debian-package

# Manual build
dpkg-buildpackage -us -uc -b
```

### CI/CD Pipeline Build

The package is automatically built in the GitLab CI pipeline:

1. **Stage**: 🧱 build
2. **Job**: `build-debian-pkg`
3. **Environment**: Ubuntu 22.04
4. **Triggers**: Main branch, develop branch, hotfix branches

### Version Management

- Package version automatically maps to GitVersion SemVer format
- Format: `ekfsm_X.Y.Z-1_all.deb`
- Changelog is automatically updated with CI information

## Optimization Features

### Size Reduction
- Removes test files, documentation, and examples from dependencies
- Deletes Python cache files (*.pyc, __pycache__)
- Compresses Python source files with gzip (except ekfsm itself)
- Removes unnecessary package metadata

### Custom Import System
- Implements gzip_importer.py for loading compressed Python files
- Automatically handles .py.gz files transparently
- Maintains full functionality while reducing disk space

### Dependency Bundling
- Creates isolated virtual environment with locked versions
- Uses uv for fast, reproducible dependency resolution
- Generates requirements.lock file for build reproducibility

## Installation

### Install from .deb file
```bash
sudo dpkg -i ekfsm_X.Y.Z-1_all.deb
sudo apt-get install -f  # Fix any missing system dependencies
```

### Verify Installation
```bash
ekfsm-cli --version
ekfsm --help  # Alternative command
```

### Uninstall
```bash
sudo apt-get remove ekfsm        # Remove package
sudo apt-get purge ekfsm         # Remove package and config files
```

## Usage

After installation, ekfsm is available system-wide:

```bash
# Primary command
ekfsm-cli [options] [commands]

# Convenience alias
ekfsm [options] [commands]

# Help
ekfsm-cli --help
```

## Python Path Integration

The package uses a .pth file to integrate with the system Python:

- **Path**: `/usr/lib/python3/dist-packages/ekfsm-bundled.pth`
- **Purpose**: Allows `import ekfsm` from any Python environment
- **Isolation**: Dependencies remain isolated in virtual environment
- **Compatibility**: Works with system Python and virtual environments

## Troubleshooting

### Import Issues
```bash
# Check if .pth file is working
python3 -c "import sys; print([p for p in sys.path if 'ekfsm' in p])"

# Verify ekfsm can be imported
python3 -c "import ekfsm; print(ekfsm.__file__)"
```

### Path Problems
```bash
# Check wrapper script
cat /usr/bin/ekfsm-cli

# Test direct execution
/opt/ekfsm/venv/bin/python -c "from ekfsm.cli import main; main()" --help
```

### Package Information
```bash
# Show package details
dpkg -s ekfsm

# List package files
dpkg -L ekfsm

# Check package integrity
debsums ekfsm
```

## Development

### Adding New Dependencies

1. Update `pyproject.toml` with new dependencies
2. The build process automatically handles locked versions
3. Test locally with `direnv exec . build-debian-package`

### Modifying Build Process

- **Control files**: [debian/control](debian/control)
- **Build rules**: [debian/rules](debian/rules)
- **Bundling script**: [scripts/bundle-dependencies.sh](scripts/bundle-dependencies.sh)
- **CI configuration**: [.gitlab-ci.yml](.gitlab-ci.yml) (build-debian-pkg job)

### Testing Locally

```bash
# Build package
dpkg-buildpackage -us -uc -b

# Install locally
sudo dpkg -i ../ekfsm_*.deb

# Test functionality
ekfsm-cli --help

# Uninstall
sudo apt-get remove ekfsm
```

## CI/CD Integration

The Debian package is integrated into the GitLab CI/CD pipeline:

### Artifacts
- **Package**: `ekfsm_X.Y.Z-1_all.deb`
- **Changes**: `ekfsm_X.Y.Z-1_all.changes`
- **Build info**: `ekfsm_X.Y.Z-1_all.buildinfo`
- **Expiry**: 30 days

### Download
Packages are available from GitLab CI artifacts:
- Navigate to Pipeline → Build → build-debian-pkg job
- Download artifacts containing the .deb file
- Or use the release page link for tagged releases

## Security Considerations

- **Isolated environment**: Dependencies don't interfere with system packages
- **No user site**: PYTHONNOUSERSITE prevents user package conflicts
- **Locked versions**: Reproducible builds prevent supply chain attacks
- **System integration**: Minimal system impact through .pth file approach
