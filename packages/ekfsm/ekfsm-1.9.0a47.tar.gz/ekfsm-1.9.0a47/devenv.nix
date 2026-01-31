{ pkgs, lib, config, inputs, ... }:
{
  env.GREET = "devenv";

  dotenv = {
    enable = true;
    disableHint = true;
  };

  cachix = {
    enable = false;
  };

  packages = [
    pkgs.texliveFull
    pkgs.git
    pkgs.gnumake
    pkgs.pre-commit
    pkgs.python3Packages.flake8
    pkgs.yamllint
    # Debian packaging tools - use system packages in CI
    pkgs.dpkg
    pkgs.fakeroot
  ];

  languages = {
    python = {
      enable = true;
      uv = {
        enable = true;
      };
    };
  };

  # Git hooks lokal nutzen, aber im CI deaktivieren
  git-hooks.enable = builtins.getEnv "CI" != "true";

  git-hooks.hooks = {
    default-version = {
      enable = true;
      name = "Ensure default version";
      entry = "git-reset-version";
      pass_filenames = false;
    };

    update-docs-requirements = {
      enable = true;
      name = "Update requirements of documentation";
      entry = "update-docs";
      pass_filenames = false;
    };

    # Remove trailing whitespace
    trailing-whitespace = {
      enable = true;
      package = pkgs.python3Packages.pre-commit-hooks;
      entry = "trailing-whitespace-fixer";
      excludes = [
        "tests/sim/sys/.*$"
        ".*\\.png$"
        ".*\\.jpeg$"
        ".*\\.svg$"
      ];
    };

    # Ensure files end with a newline
    end-of-file-fixer.enable = true;

    # Check YAML syntax
    check-yaml.enable = true;

    # Run Flake8 for Python linting
    flake8.enable = true;

    shellcheck.enable = true;
  };

  scripts.sast-scan.exec = ''
    uv run bandit -f json -r ekfsm -c .bandit --severity-level low --confidence-level medium -o bandit-report.json
  '';

  scripts.bandit-scan.exec = ''
    uv run bandit -r ekfsm -c .bandit
  '';

  scripts.audit-scan.exec = ''
    generate-prod-reqs
    uv run pip-audit --requirement prod-requirements.txt -f cyclonedx-json -o gl-sbom.json
    uv run pip-audit --requirement prod-requirements.txt -f json -o gl-dependency-scanning-report.json
  '';

  scripts.update-docs.exec = ''
    temp_file=$(mktemp)
    trap "rm -f $temp_file" 0 2 3 15
    uv export > $temp_file 2>/dev/null

    if diff -q $temp_file docs/requirements.txt &>/dev/null; then
      update-doc-reqs

      if git diff --cached --name-only | grep -q -- 'uv.lock'; then
        git add docs/requirements.txt
      fi
    fi
  '';

  scripts.git-reset-version.exec = ''
      if git diff --cached --name-only | grep -q -- "^pyproject.toml"; then
        uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version 0.0.0 && git add pyproject.toml
      fi
  '';

  scripts.bump-version.exec = ''
    uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version $(uvx dunamai from any --no-metadata --style semver)
  '';

  scripts.generate-package.exec = ''
    bump-version
    uv build
  '';

  scripts.test-bundling.exec = ''
    echo "Testing dependency bundling..."

    # Clean previous test
    rm -rf test-bundle/ || true

    # Create test directory
    mkdir -p test-bundle/ekfsm

    # Generate locked requirements
    uv pip compile pyproject.toml --output-file requirements.lock
    echo "✓ Generated requirements.lock"

    # Create test virtual environment
    python3 -m venv test-bundle/ekfsm/opt/ekfsm/venv
    echo "✓ Created virtual environment"

    # Install dependencies
    test-bundle/ekfsm/opt/ekfsm/venv/bin/pip install --upgrade pip
    test-bundle/ekfsm/opt/ekfsm/venv/bin/pip install --no-cache-dir -r requirements.lock
    test-bundle/ekfsm/opt/ekfsm/venv/bin/pip install --no-cache-dir --no-deps .
    echo "✓ Installed dependencies and ekfsm"

    # Test the installation
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    SITE_PACKAGES="test-bundle/ekfsm/opt/ekfsm/venv/lib/python$PYTHON_VERSION/site-packages"

    echo "✓ Testing ekfsm import..."
    test-bundle/ekfsm/opt/ekfsm/venv/bin/python -c "
import sys
sys.path.insert(0, '$SITE_PACKAGES')
import ekfsm
print(f'✓ ekfsm version: {ekfsm.__version__ if hasattr(ekfsm, \"__version__\") else \"unknown\"}')
print(f'✓ ekfsm location: {ekfsm.__file__}')
"

    echo ""
    echo "Bundle test completed successfully!"
    echo "Test environment: test-bundle/ekfsm/"
    echo "Virtual env size: $(du -sh test-bundle/ekfsm/opt/ekfsm/venv | cut -f1)"
    echo ""
    echo "Cleanup: rm -rf test-bundle/"
  '';

  scripts.build-debian-package.exec = ''
    echo "Note: This is a simplified local build. Full .deb build happens in CI with proper Ubuntu environment."

    # Ensure we have the latest version
    bump-version

    # Update debian changelog with current version
    CURRENT_VERSION=$(uvx dunamai from any --no-metadata --style semver)
    TIMESTAMP=$(date -R)

    # Create new changelog entry (replace existing to avoid duplicates)
    cat > debian/changelog << EOF
ekfsm ($CURRENT_VERSION-1) stable; urgency=medium

  * Release version $CURRENT_VERSION
  * Automated build from development environment
  * Single-artifact deployment with bundled dependencies
  * High compression packaging for minimal size

 -- Jan Jansen <jan@ekf.de>  $TIMESTAMP
EOF

    # Generate locked requirements for reproducible builds
    uv pip compile pyproject.toml --output-file requirements.lock

    # Clean any previous build artifacts
    rm -rf debian/ekfsm/ || true

    # Run our bundling script to prepare the package structure
    chmod +x scripts/bundle-dependencies.sh
    ./scripts/bundle-dependencies.sh

    echo ""
    echo "✅ Package structure prepared successfully!"
    echo ""
    echo "To build actual .deb package:"
    echo "  1. On Ubuntu/Debian system: ./scripts/build-deb.sh"
    echo "  2. In GitLab CI: Pipeline will auto-build on push"
    echo ""
    echo "Package structure preview:"
    find debian/ekfsm -type f | head -20 || echo "Run ./scripts/bundle-dependencies.sh first"
    echo ""
    echo "Version: $CURRENT_VERSION"
    echo "Changelog updated: debian/changelog"
    echo "Dependencies locked: requirements.lock"
  '';

  scripts.publish-package.exec = ''
    uv publish
  '';

  scripts.generate-prod-reqs.exec = ''
    uv pip compile pyproject.toml --output-file prod-requirements.txt
  '';

  scripts.generate-doc-reqs.exec = ''
    uv export > docs/requirements.txt
  '';

  scripts.generate-coverage.exec = ''
    if [ "$EUID" -ne 0 ]; then
      uv run --with pytest-cov pytest -k 'not locking' --cov=ekfsm --cov --cov-report term --cov-report xml:coverage.xml | perl -pe 's/\e\[?.*?[\@-~]//g' | tee pytest.log
      uv run --with pytest-cov pytest -k 'not locking' --cov=ekfsm --junitxml=report.xml
    else
      uv run --with pytest-cov pytest --cov=ekfsm --cov --cov-report term --cov-report xml:coverage.xml | perl -pe 's/\e\[?.*?[\@-~]//g' | tee pytest.log
      uv run --with pytest-cov pytest --cov=ekfsm --junitxml=report.xml
    fi
  '';

  scripts.doc-coverage.exec = ''
    uv run make -C docs/ coverage
  '';

  scripts.doc-man-pages.exec = ''
    uv run make -C docs/ man
  '';

  scripts.doc-pdf.exec = ''
    uv run make -C docs/ latexpdf
  '';

  scripts.doc-html.exec = ''
    uv run make -C docs/ html
  '';

  scripts.doc-clean.exec = ''
    uv run make -C docs/ clean
  '';

  scripts.lint.exec = ''
    uvx flake8 --exclude .venv,dist,.devenv
  '';

  scripts.typing.exec = ''
    uv run mypy ekfsm
  '';

  enterShell = ''
    if [ ! -f .git/hooks/pre-commit ]; then
      pre-commit install
      echo "Pre-commit hooks installed."
    fi
    if [ -d .devenv/state/venv ]; then
      source .devenv/state/venv/bin/activate
    else
      echo "No virtual environment found. Package must be generated first."
    fi
  '';

  enterTest = ''
    echo "Running tests"
  '';

}
