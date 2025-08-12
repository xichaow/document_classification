#!/bin/bash

# Document Classification System - Deployment Preparation Script
echo "🚀 Preparing Document Classification System for Render deployment..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p results  
mkdir -p src/data

# Check if required files exist
echo "🔍 Checking required files..."
files=(
    "requirements.txt"
    "main.py"
    "render.yaml"
    "Dockerfile"
    ".dockerignore"
)

missing_files=()
for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -ne 0 ]]; then
    echo "❌ Missing required files:"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

echo "✅ All required files present"

# Validate Python syntax
echo "🐍 Validating Python syntax..."
if command -v python3 &> /dev/null; then
    python3 -m py_compile main.py
    if [[ $? -ne 0 ]]; then
        echo "❌ Python syntax errors in main.py"
        exit 1
    fi
    echo "✅ Python syntax validation passed"
else
    echo "⚠️  Python3 not found, skipping syntax validation"
fi

# Test requirements.txt
echo "📦 Testing requirements.txt..."
if command -v pip &> /dev/null; then
    pip check > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        echo "⚠️  Some dependency conflicts detected, but continuing..."
    else
        echo "✅ Dependencies check passed"
    fi
fi

# Create .env template if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# AWS Configuration (Optional - for full functionality)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000
EOL
    echo "✅ Created .env template"
fi

# Check git repository
if [[ -d ".git" ]]; then
    echo "✅ Git repository detected"
    
    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        echo "⚠️  You have uncommitted changes. Consider committing before deployment."
    fi
    
    # Show current branch
    current_branch=$(git branch --show-current)
    echo "📍 Current branch: $current_branch"
else
    echo "⚠️  No git repository found. You'll need to push to GitHub for Render deployment."
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. 📤 Push your code to GitHub"
echo "2. 🌐 Go to render.com and create a new Blueprint or Web Service"
echo "3. 🔗 Connect your GitHub repository"
echo "4. ⚙️  Set environment variables (AWS credentials, etc.)"
echo "5. 🚀 Deploy!"
echo ""
echo "📚 See DEPLOYMENT.md for detailed instructions"