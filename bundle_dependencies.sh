#!/bin/bash
# Script to bundle dependencies for Anki addon

# Exit on error
set -e

echo "=== Bundling dependencies for Anki addon ==="
echo "This script will create a Python 3.13 venv and bundle pydantic and qdrant for Anki"

# Ensure Python 3.13 is available via uv
echo "Ensuring Python 3.13 is available..."
uv python install 3.13

# Create a temporary virtual environment with Python 3.13
BUNDLE_VENV=".venv_bundle"
echo "Creating temporary virtual environment with Python 3.13..."
uv venv "$BUNDLE_VENV" --python 3.13

# Install pydantic and qdrant into the virtual environment
echo "Installing pydantic and qdrant..."
# No version pin is needed: Anki 26.x ships typing_extensions >= 4.16, so the
# vendored pydantic no longer needs to avoid the typing_extensions dependency
# (older Anki versions bundled a typing_extensions that could not be overridden).
uv pip install --python "$BUNDLE_VENV/bin/python" pydantic qdrant-client

# Create or clean vendor directory
echo "Preparing vendor directory..."
mkdir -p vendor
rm -rf vendor/*

# Copy the site-packages from the venv to vendor directory
echo "Copying dependencies to vendor directory..."
SITE_PACKAGES="$("$BUNDLE_VENV/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
cp -r "$SITE_PACKAGES/"* vendor/

# Clean up the temporary venv
echo "Cleaning up..."
rm -rf "$BUNDLE_VENV"

echo "=== Bundling complete! ==="
echo "pydantic, qdrant, and their dependencies are now available in the vendor directory"
