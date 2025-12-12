# Installation Guide

## Python Version

This project targets **Python 3.11** as specified in the AWS SAM template. While it may work with Python 3.12+, some packages may not have pre-built wheels for Python 3.13+ and may require Rust compilation.

## Recommended: Use Python 3.11

### Using pyenv (recommended)

```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python 3.11
pyenv install 3.11.10

# Set local Python version
cd /Users/yacoubosman/Projects/smsbot
pyenv local 3.11.10

# Verify
python --version  # Should show 3.11.10
```

### Using conda

```bash
# Create environment with Python 3.11
conda create -n smsbot python=3.11
conda activate smsbot
```

## Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Troubleshooting Build Errors

If you encounter build errors (especially for `pydantic-core`, `lxml`, or `tiktoken`):

### Option 1: Use Python 3.11 (Recommended)
As mentioned above, Python 3.11 has the best package support.

### Option 2: Install Rust (for Python 3.13+)
If you must use Python 3.13, you can install Rust to build packages:

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Then try installing again
pip install -r requirements.txt
```

### Option 3: Use Pre-built Wheels
Try upgrading pip and using the latest package versions:

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Verify Installation

```bash
# Test imports
python -c "import fastapi; import openai; import pinecone; print('✓ All imports successful')"
```

