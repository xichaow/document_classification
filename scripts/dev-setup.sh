#!/bin/bash

# Document Classification System - Development Setup Script

echo "🚀 Setting up Document Classification System for development..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv_linux" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_linux
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv_linux/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/uploads data/results

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your AWS credentials (optional)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. 📝 Edit .env file with your AWS credentials (optional)"
echo "2. 🚀 Run: python main.py"
echo "3. 🌐 Open: http://localhost:8000"
echo ""
echo "For deployment to Render, see: docs/DEPLOYMENT.md"