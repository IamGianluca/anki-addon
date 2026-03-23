#!/bin/bash
# Script to bundle dependencies for Anki addon

# Exit on error
set -e

echo "=== Bundling dependencies for Anki addon ==="
echo "This script will create a Python 3.9 venv and bundle pydantic and qdrant for Anki"

# Ensure Python 3.9 is available via uv
echo "Ensuring Python 3.9 is available..."
uv python install 3.9

# Create a temporary virtual environment with Python 3.9
BUNDLE_VENV=".venv_bundle"
echo "Creating temporary virtual environment with Python 3.9..."
uv venv "$BUNDLE_VENV" --python 3.9

# Install pydantic into the virtual environment
echo "Installing pydantic and qdrant..."
# pydantic>=2.10 requires typing_extensions>=4.6.0 (for Sentinel). Anki ships an
# older typing_extensions that is already loaded into sys.modules before the addon
# runs, so the vendored version cannot override it. pydantic<2.10 uses
# pydantic-core<2.27 which avoids this dependency.
uv pip install --python "$BUNDLE_VENV/bin/python" "pydantic<2.10" qdrant-client

# Create or clean vendor directory
echo "Preparing vendor directory..."
mkdir -p vendor
rm -rf vendor/*

# Copy the site-packages from the venv to vendor directory
echo "Copying dependencies to vendor directory..."
cp -r "$BUNDLE_VENV/lib/python3.9/site-packages/"* vendor/

# Clean up the temporary venv
echo "Cleaning up..."
rm -rf "$BUNDLE_VENV"

echo "=== Bundling complete! ==="
echo "pydantic, qdrant, and their dependencies are now available in the vendor directory"
