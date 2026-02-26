#!/bin/bash

# Run the new A2UI-compliant image generation server

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env with your GOOGLE_API_KEY or GEMINI_API_KEY"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Run the server
echo "Starting A2UI Image Generation Server..."
echo "Using official a2ui and a2a-sdk packages"
echo ""
python server_new.py --host localhost --port 10002
