#!/bin/bash

# One-click deployment script for RAG Agent to Render
# This script provides instructions and validation for Render deployment

set -e  # Exit on any error

echo "🚀 RAG Agent PM - Render Deployment Script"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "render.yaml" ] || [ ! -f "app.py" ] || [ ! -f "vectorization_api.py" ]; then
    echo "❌ Error: This script must be run from the RAG agent root directory"
    echo "   Required files: render.yaml, app.py, vectorization_api.py"
    exit 1
fi

echo "✅ Found required files"

# Check if git repository is up to date
echo ""
echo "🔍 Checking Git repository status..."

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "   Please commit and push changes before deploying"
    
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Deployment cancelled"
        exit 1
    fi
fi

# Check if we can reach origin
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Git repository is accessible"
else
    echo "❌ Error: Cannot access Git remote repository"
    echo "   Please ensure you're connected to the internet and have access to the repository"
    exit 1
fi

# Display repository information
REPO_URL=$(git config --get remote.origin.url)
CURRENT_BRANCH=$(git branch --show-current)
LATEST_COMMIT=$(git log -1 --format="%h %s")

echo ""
echo "📋 Repository Information:"
echo "   URL: $REPO_URL"
echo "   Branch: $CURRENT_BRANCH"
echo "   Latest commit: $LATEST_COMMIT"

# Check required environment variables
echo ""
echo "🔐 Environment Variables Checklist:"
echo "   You will need these API keys for deployment:"

required_vars=("OPENAI_API_KEY" "DATABASE_URL")
optional_vars=("ANTHROPIC_API_KEY" "COHERE_API_KEY" "GROQ_API_KEY")

echo ""
echo "   Required:"
for var in "${required_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "   ✅ $var (found in current environment)"
    else
        echo "   ⚠️  $var (not found - you'll need to set this in Render)"
    fi
done

echo ""
echo "   Optional:"
for var in "${optional_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "   ✅ $var (found in current environment)"
    else
        echo "   ℹ️  $var (not found - optional)"
    fi
done

# Display deployment URLs that will be created
echo ""
echo "🌐 Expected Deployment URLs:"
echo "   Main RAG API: https://rag-agent-api.onrender.com"
echo "   Vectorization API: https://rag-vectorization-api.onrender.com"
echo "   (Actual URLs may vary based on availability)"

# Display next steps
echo ""
echo "📝 Manual Deployment Steps:"
echo "   1. Go to https://dashboard.render.com/"
echo "   2. Create PostgreSQL database first (see RENDER_DEPLOYMENT_GUIDE.md)"
echo "   3. Create two web services using the repository: $REPO_URL"
echo "   4. Configure environment variables for both services"
echo "   5. Deploy and test endpoints"

echo ""
echo "📖 For detailed instructions, see:"
echo "   - RENDER_DEPLOYMENT_GUIDE.md (complete step-by-step guide)"
echo "   - render.yaml (service configuration)"

# Offer to open deployment guide
echo ""
read -p "📚 Open deployment guide now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open > /dev/null; then
        open "RENDER_DEPLOYMENT_GUIDE.md"
    elif command -v xdg-open > /dev/null; then
        xdg-open "RENDER_DEPLOYMENT_GUIDE.md"
    else
        echo "   Please manually open: RENDER_DEPLOYMENT_GUIDE.md"
    fi
fi

# Offer to run tests after deployment
echo ""
echo "🧪 After deployment, run tests with:"
echo "   python test_deployment.py"

# Final checklist
echo ""
echo "✅ Pre-deployment Checklist Complete:"
echo "   - Repository is accessible ✅"
echo "   - Configuration files are present ✅"
echo "   - Environment variables identified ✅"
echo "   - Deployment guide available ✅"

echo ""
echo "🎯 Next: Follow the manual steps in RENDER_DEPLOYMENT_GUIDE.md"
echo "   The render.yaml file will automatically configure both services"

echo ""
echo "🚀 Ready for deployment!"