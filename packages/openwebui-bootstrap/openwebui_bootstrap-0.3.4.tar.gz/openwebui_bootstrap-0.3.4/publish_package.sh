#!/bin/bash

# Open WebUI Bootstrap Package Publishing Script
# This script builds and publishes the package to PyPI

# Exit immediately if any command fails
set -e

# Function to display error messages
error_exit() {
    echo "❌ $1" 1>&2
    exit 1
}

# Function to display success messages
success_msg() {
    echo "✅ $1"
}

# Function to display info messages
info_msg() {
    echo "ℹ️  $1"
}

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ]; then
    error_exit "This script must be run from the project root directory"
fi

# Check if the package version is set
PACKAGE_VERSION=$(grep -E '^version\s*=' pyproject.toml | cut -d '"' -f 2)
if [ -z "$PACKAGE_VERSION" ]; then
    error_exit "Could not determine package version from pyproject.toml"
fi

info_msg "Starting Open WebUI Bootstrap package publishing process..."
info_msg "Package version: $PACKAGE_VERSION"

# Step 1: Clean up any previous build artifacts
info_msg "Cleaning up previous build artifacts..."
rm -rf dist/ || true
rm -rf build/ || true
success_msg "Cleaned up build artifacts"

# Step 2: Build the package
info_msg "Building package..."
# Check if hatchling is installed, install if not
if ! uv run python -c "import hatchling" 2>/dev/null; then
    info_msg "Installing hatchling build backend..."
    uv add hatchling
fi
uv run python -m build
success_msg "Package built successfully"

# Step 3: Check if the package was built
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    error_exit "No distribution files were created"
fi

# List the built packages
info_msg "Built packages:"
ls -lh dist/

# Step 4: Run comprehensive tests
info_msg "Running comprehensive test suite..."
uv run pytest tests/ -v
if [ $? -eq 0 ]; then
    success_msg "✅ All tests passed successfully"
else
    error_exit "❌ Tests failed - aborting publication"
fi

# Step 5: Verify the package can be installed locally first
info_msg "Testing local installation..."
uv pip install dist/openwebui_bootstrap-$PACKAGE_VERSION.tar.gz --force-reinstall --no-deps
if [ $? -eq 0 ]; then
    success_msg "Local installation test passed"
else
    error_exit "Local installation test failed"
fi

# Step 6: Check if twine is available
if ! command -v twine &> /dev/null; then
    info_msg "Installing twine for package publishing..."
    uv pip install twine
    success_msg "Twine installed"
fi

# Step 6: Check if package is already published (optional check)
info_msg "Checking if package version is already published on PyPI..."
PACKAGE_EXISTS=$(uv run python -c "import urllib.request; import json; response = urllib.request.urlopen('https://pypi.org/pypi/openwebui-bootstrap/json'); data = json.loads(response.read()); versions = data.get('releases', {}).keys(); print('yes' if '$PACKAGE_VERSION' in versions else 'no')" 2>/dev/null || echo "no")

if [ "$PACKAGE_EXISTS" = "yes" ]; then
    error_exit "Package version $PACKAGE_VERSION is already published on PyPI"
else
    success_msg "Package version $PACKAGE_VERSION is not yet published"
fi

# Step 7: Final confirmation before publishing
echo ""
echo "🚀 READY TO PUBLISH TO PyPI"
echo "==========================="
echo "Package: openwebui-bootstrap"
echo "Version: $PACKAGE_VERSION"
echo "Files to be published:"
ls -lh dist/
echo ""
echo "✅ All tests passed"
echo "✅ Local installation successful"
echo "✅ Package built successfully"
echo ""
read -p "Do you want to proceed with publishing to PyPI? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info_msg "Publication cancelled by user"
    exit 0
fi

# Step 8: Publish to PyPI
info_msg "Publishing to PyPI..."
echo "🔑 Please enter your PyPI credentials when prompted..."

# Use twine to upload to PyPI
uv run twine upload dist/*

# Step 8: Verify publication
info_msg "Verifying publication..."
sleep 10  # Wait for PyPI to process the upload

# Try to install from PyPI
uv pip install --upgrade openwebui-bootstrap==$PACKAGE_VERSION --force-reinstall
if [ $? -eq 0 ]; then
    success_msg "✅ Package successfully published and installed from PyPI!"
    success_msg "🎉 Open WebUI Bootstrap $PACKAGE_VERSION is now available on PyPI!"
else
    error_exit "Package installation from PyPI failed"
fi

# Display package info
info_msg "Package information:"
uv run pip show openwebui-bootstrap

echo ""
echo "🎉 Publishing complete!"
echo "Package URL: https://pypi.org/project/openwebui-bootstrap/$PACKAGE_VERSION/"
