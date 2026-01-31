#!/bin/bash
# Publish to PyPI using uv, extracting token from ~/.pypirc

set -e

PYPIRC="$HOME/.pypirc"

if [[ ! -f "$PYPIRC" ]]; then
    echo "Error: ~/.pypirc not found"
    echo "Create it with:"
    echo "  [pypi]"
    echo "  username = __token__"
    echo "  password = pypi-YOUR_TOKEN"
    exit 1
fi

# Extract token from .pypirc (handles both "password = token" and "password=token")
TOKEN=$(awk '/^\[pypi\]/{found=1} found && /^password/{sub(/^password[ ]*=[ ]*/, ""); print; exit}' "$PYPIRC")

if [[ -z "$TOKEN" ]]; then
    echo "Error: Could not extract password from ~/.pypirc [pypi] section"
    exit 1
fi

# Clean and rebuild
echo "Cleaning dist/"
rm -rf dist/

echo "Building package..."
uv build

echo "Publishing to PyPI..."
uv publish --token "$TOKEN"

echo "Done!"
