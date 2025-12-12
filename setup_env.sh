#!/bin/bash
# Setup script for SMS Bot project

echo "Setting up SMS Bot development environment..."

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "Using conda..."
    conda create -n smsbot python=3.11 -y
    echo ""
    echo "✓ Environment created!"
    echo ""
    echo "To activate:"
    echo "  conda activate smsbot"
    echo ""
    echo "Then install dependencies:"
    echo "  pip install -r requirements.txt"
elif command -v pyenv &> /dev/null; then
    echo "Using pyenv..."
    pyenv install 3.11.10 -s
    pyenv local 3.11.10
    echo ""
    echo "✓ Python 3.11.10 installed and set for this project!"
    echo ""
    echo "Install dependencies:"
    echo "  pip install -r requirements.txt"
else
    echo "Neither conda nor pyenv found."
    echo ""
    echo "Option 1: Install conda"
    echo "  brew install miniconda"
    echo ""
    echo "Option 2: Install pyenv"
    echo "  brew install pyenv"
    echo "  pyenv install 3.11.10"
    echo "  pyenv local 3.11.10"
    echo ""
    echo "Option 3: Install Rust (for Python 3.13)"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
fi

