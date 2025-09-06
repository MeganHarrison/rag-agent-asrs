#!/bin/bash

# Startup script for RAG Agent PM Vectorization API
# This runs alongside the main agent to handle vectorization requests

set -e

echo "Starting RAG Agent PM Vectorization API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data if needed
python -c "import nltk; nltk.download('punkt', quiet=True)"

# Check environment variables
if [ -z "$DATABASE_URL" ]; then
    if [ -f ".env" ]; then
        echo "Loading environment from .env file..."
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo "Warning: DATABASE_URL not set and .env file not found"
    fi
fi

# Run database migrations
echo "Running database migrations..."
if [ -f "sql/run_migrations.sh" ]; then
    ./sql/run_migrations.sh
else
    echo "Migration script not found, skipping..."
fi

# Apply unified schema
if [ -f "sql/unified_schema.sql" ]; then
    echo "Applying unified schema..."
    psql $DATABASE_URL -f sql/unified_schema.sql || echo "Schema may already exist, continuing..."
fi

# Start the vectorization API
echo "Starting Vectorization API on port 8000..."
uvicorn vectorization_api:app --host 0.0.0.0 --port 8000 --reload