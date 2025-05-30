#!/bin/bash
# Script to bundle dependencies for Anki addon

# Exit on error
set -e

echo "=== Bundling dependencies for Anki addon ==="
echo "This script will create a Python 3.9 venv and bundle pydantic and qdrant for Anki"

# Check if Python 3.9 is available
if ! command -v python3.9 &> /dev/null; then
    echo "Error: Python 3.9 is required but not found"
    echo "Please install Python 3.9 and try again"
    exit 1
fi

# Clean up existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create a temporary virtual environment with Python 3.9
echo "Creating virtual environment with Python 3.9..."
uv venv .venv --python python3.9

# Install pydantic into the virtual environment
echo "Installing pydantic and qdrant..."
uv pip install --python .venv/bin/python pydantic qdrant-client

# Create or clean vendor directory
echo "Preparing vendor directory..."
mkdir -p vendor
rm -rf vendor/*

# Copy the site-packages from the venv to vendor directory
echo "Copying dependencies to vendor directory..."
cp -r .venv/lib/python3.9/site-packages/* vendor/

# Clean up the temporary venv
echo "Cleaning up..."
rm -rf .venv

echo "=== Bundling complete! ==="
echo "pydantic, qdrant, and their dependencies are now available in the vendor directory"
