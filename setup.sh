#!/bin/bash

# Setup script for A2UI Image Generation Agent

echo "🚀 Setting up A2UI Image Generation Agent..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GOOGLE_API_KEY"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run the server: python server.py"
echo "  4. Test with: python client_example.py"
echo ""
