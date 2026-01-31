#!/bin/bash
set -e

echo "iFrp Installer"
echo "=============="

# Check for package managers and install
if command -v pipx &> /dev/null; then
    echo "Installing with pipx..."
    pipx install ifrp
elif command -v uv &> /dev/null; then
    echo "Installing with uv..."
    uv tool install ifrp
elif command -v pip3 &> /dev/null; then
    echo "Installing with pip3..."
    pip3 install --user ifrp
elif command -v pip &> /dev/null; then
    echo "Installing with pip..."
    pip install --user ifrp
else
    echo "Error: No Python package manager found."
    echo "Please install Python 3.10+ and pip first."
    exit 1
fi

echo ""
echo "Installation complete!"
echo "Run 'ifrp' to start the TUI."
