#!/bin/bash
# Start script for SMS Bot API server

set -e

echo "Starting SMS Bot API server..."

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    # Use a safer method to load .env (handles values with spaces/special chars)
    set -a
    source .env
    set +a
    echo "✓ Environment variables loaded from .env"
fi

# Set AWS region if not set
export AWS_REGION=${AWS_REGION:-us-east-1}

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check which AWS credential method is being used
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Using AWS credentials from .env file (AWS_ACCESS_KEY_ID)"
    # Verify credentials work
    if aws sts get-caller-identity > /dev/null 2>&1; then
        IDENTITY=$(aws sts get-caller-identity 2>/dev/null)
        ACCOUNT=$(echo "$IDENTITY" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
        echo "✓ AWS credentials valid - Account: $ACCOUNT"
    else
        echo "⚠️  Warning: AWS credentials from .env appear to be invalid or expired"
        echo "  Please update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
    fi
elif [ -n "$AWS_PROFILE" ]; then
    echo "Using AWS profile: $AWS_PROFILE"
    # Verify AWS credentials are available
    if aws sts get-caller-identity --profile "$AWS_PROFILE" > /dev/null 2>&1; then
        echo "✓ AWS credentials valid"
        IDENTITY=$(aws sts get-caller-identity --profile "$AWS_PROFILE" 2>/dev/null)
        ACCOUNT=$(echo "$IDENTITY" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
        echo "  Account: $ACCOUNT"
    else
        echo "⚠️  Warning: AWS credentials expired or not found for profile: $AWS_PROFILE"
        echo "  Attempting SSO login..."
        if aws sso login --profile "$AWS_PROFILE" 2>&1; then
            echo "✓ SSO login successful"
        else
            echo "  Please run manually: aws sso login --profile $AWS_PROFILE"
            echo "  Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
        fi
    fi
else
    # No credentials set - try default
    echo "No AWS credentials found in .env, trying default credentials..."
    AWS_PROFILE=${AWS_PROFILE:-rise-admin4}
    export AWS_PROFILE
    if aws sts get-caller-identity --profile "$AWS_PROFILE" > /dev/null 2>&1; then
        echo "✓ Using default profile: $AWS_PROFILE"
    else
        echo "⚠️  Warning: No valid AWS credentials found"
        echo "  Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
    fi
fi

# Start the server
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "Admin dashboard: http://localhost:8000/admin"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

PYTHONPATH="$(pwd)/src:$PYTHONPATH" uvicorn src.api.main:app --reload --port 8000

