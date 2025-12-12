#!/bin/bash
# Kill existing server and restart with correct configuration

echo "Stopping existing uvicorn servers..."
pkill -f "uvicorn src.api.main" || echo "No existing server found"

sleep 2

echo "Starting server with AWS profile configuration..."
./start_server.sh

