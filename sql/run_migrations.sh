#!/bin/bash

# Database Migration Script for RAG Agent PM
# This script runs all necessary SQL migrations for the enhanced RAG system

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting database migrations for RAG Agent PM...${NC}"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}DATABASE_URL not set. Trying to load from .env file...${NC}"
    if [ -f "../.env" ]; then
        export $(cat ../.env | grep DATABASE_URL | xargs)
    elif [ -f ".env" ]; then
        export $(cat .env | grep DATABASE_URL | xargs)
    else
        echo -e "${RED}Error: DATABASE_URL not found in environment or .env file${NC}"
        echo "Please set DATABASE_URL or create .env file with:"
        echo "DATABASE_URL=postgresql://user:password@host:port/database"
        exit 1
    fi
fi

# Parse DATABASE_URL for psql command
# Format: postgresql://user:password@host:port/database
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    echo -e "${RED}Error: Could not parse DATABASE_URL${NC}"
    exit 1
fi

echo -e "${YELLOW}Connecting to database: $DB_NAME on $DB_HOST:$DB_PORT${NC}"

# Export for psql
export PGPASSWORD=$DB_PASSWORD

# Function to run SQL file
run_sql_file() {
    local file=$1
    local description=$2
    
    echo -e "${YELLOW}Running: $description${NC}"
    
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $file > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $description completed${NC}"
        return 0
    else
        echo -e "${RED}✗ $description failed${NC}"
        echo -e "${RED}Error details:${NC}"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $file
        return 1
    fi
}

# Run migrations in order
echo -e "\n${GREEN}Step 1: Creating base schema...${NC}"
if [ -f "schema.sql" ]; then
    run_sql_file "schema.sql" "Base schema creation"
else
    echo -e "${YELLOW}Base schema already exists or schema.sql not found, skipping...${NC}"
fi

echo -e "\n${GREEN}Step 2: Creating conversation memory schema...${NC}"
run_sql_file "conversation_memory.sql" "Conversation memory tables and functions"

echo -e "\n${GREEN}Step 3: Adding enhanced search functions...${NC}"

# Create additional search functions
cat << 'EOF' | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
-- Enhanced search with metadata filtering
CREATE OR REPLACE FUNCTION enhanced_match_chunks(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    project_filter INT DEFAULT NULL,
    date_after TIMESTAMP DEFAULT NULL,
    doc_type_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source,
        d.created_at
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
        AND (project_filter IS NULL OR (d.metadata->>'project_id')::INT = project_filter)
        AND (date_after IS NULL OR d.created_at >= date_after)
        AND (doc_type_filter IS NULL OR d.metadata->>'document_type' = doc_type_filter)
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Index for metadata filtering
CREATE INDEX IF NOT EXISTS idx_documents_metadata_project ON documents ((metadata->>'project_id'));
CREATE INDEX IF NOT EXISTS idx_documents_metadata_type ON documents ((metadata->>'document_type'));

-- Add document_type column if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' 
                   AND column_name = 'document_type') THEN
        ALTER TABLE documents ADD COLUMN document_type TEXT DEFAULT 'document';
    END IF;
END $$;

-- Add project_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' 
                   AND column_name = 'project_id') THEN
        ALTER TABLE documents ADD COLUMN project_id INTEGER;
    END IF;
END $$;

GRANT ALL ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO CURRENT_USER;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Enhanced search functions created${NC}"
else
    echo -e "${RED}✗ Failed to create enhanced search functions${NC}"
fi

echo -e "\n${GREEN}Step 4: Verifying installation...${NC}"

# Verify tables exist
TABLES=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('conversations', 'conversation_messages', 'conversation_facts', 
                       'conversation_retrievals', 'conversation_summaries', 
                       'documents', 'chunks');")

if [ $TABLES -ge 7 ]; then
    echo -e "${GREEN}✓ All required tables exist${NC}"
else
    echo -e "${YELLOW}⚠ Some tables may be missing. Found $TABLES/7 expected tables${NC}"
fi

# Check for vector extension
VECTOR_EXT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';")

if [ $VECTOR_EXT -eq 1 ]; then
    echo -e "${GREEN}✓ pgvector extension is installed${NC}"
else
    echo -e "${RED}✗ pgvector extension not found. Installing...${NC}"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Database migration completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Summary:${NC}"
echo -e "  • Base schema: Ready"
echo -e "  • Conversation memory: Ready"
echo -e "  • Enhanced search: Ready"
echo -e "  • Vector extension: Ready"
echo -e "\n${GREEN}Your RAG system database is now fully configured!${NC}"

# Cleanup
unset PGPASSWORD