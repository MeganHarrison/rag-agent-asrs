-- Unified Schema for RAG System
-- This creates a unified document-based structure replacing the meeting-specific tables

-- Ensure extensions are available
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop old meeting-specific tables if migrating
DROP TABLE IF EXISTS meeting_chunks CASCADE;
DROP TABLE IF EXISTS meeting_embeddings CASCADE;
DROP TABLE IF EXISTS meetings CASCADE;

-- Ensure projects table exists (keep existing structure)
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    client_id INTEGER,
    budget NUMERIC,
    budget_used NUMERIC,
    category TEXT,
    aliases TEXT[],
    keywords TEXT[],
    team_members TEXT[],
    stakeholders TEXT[],
    address TEXT,
    state TEXT,
    phase TEXT,
    current_phase TEXT,
    completion_percentage INTEGER,
    "start date" DATE,
    "est completion" DATE,
    "est revenue" NUMERIC,
    "est profit" NUMERIC,
    "job number" TEXT,
    onedrive TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced documents table (unified for all content types)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source TEXT NOT NULL,  -- File path, URL, or identifier
    content TEXT NOT NULL,
    document_type TEXT DEFAULT 'document' CHECK (document_type IN ('meeting', 'document', 'manual', 'email', 'chat')),
    project_id INTEGER REFERENCES projects(id),
    
    -- Meeting-specific fields (null for non-meeting documents)
    meeting_date DATE,
    participants TEXT[],
    duration_minutes INTEGER,
    meeting_platform TEXT,  -- 'fireflies', 'teams', 'zoom', etc.
    meeting_id TEXT,  -- External meeting ID (fireflies_id, etc.)
    
    -- Common metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    category TEXT,
    
    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chunks table remains the same
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    chunk_index INTEGER NOT NULL,
    chunk_type TEXT DEFAULT 'standard',  -- 'standard', 'semantic', 'hierarchical', 'sentence_window'
    
    -- Hierarchical chunking support
    parent_chunk_id UUID REFERENCES chunks(id),
    depth_level INTEGER DEFAULT 0,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    start_position INTEGER,  -- Character position in original document
    end_position INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- AI insights table (for extracted facts, action items, etc.)
CREATE TABLE IF NOT EXISTS ai_insights (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id),
    insight_type TEXT CHECK (insight_type IN ('action_item', 'decision', 'risk', 'milestone', 'fact')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 0.5,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    assigned_to TEXT,
    due_date DATE,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_meeting_date ON documents(meeting_date) WHERE meeting_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS idx_chunks_parent ON chunks(parent_chunk_id) WHERE parent_chunk_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm ON chunks USING GIN (content gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_insights_document ON ai_insights(document_id);
CREATE INDEX IF NOT EXISTS idx_insights_project ON ai_insights(project_id);
CREATE INDEX IF NOT EXISTS idx_insights_type ON ai_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_assigned ON ai_insights(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_insights_due_date ON ai_insights(due_date) WHERE due_date IS NOT NULL;

-- Enhanced search function with document type support
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    project_filter INT DEFAULT NULL,
    doc_type_filter TEXT DEFAULT NULL,
    date_after TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_type TEXT,
    project_id INT
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
        c.metadata || d.metadata AS metadata,
        d.title AS document_title,
        d.document_type,
        d.project_id
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
        AND d.processing_status = 'completed'
        AND (project_filter IS NULL OR d.project_id = project_filter)
        AND (doc_type_filter IS NULL OR d.document_type = doc_type_filter)
        AND (date_after IS NULL OR d.created_at >= date_after)
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to convert meetings to documents (for migration)
CREATE OR REPLACE FUNCTION migrate_meetings_to_documents()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    migrated_count INTEGER := 0;
BEGIN
    -- Only run if meetings table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meetings') THEN
        INSERT INTO documents (
            id,
            title,
            source,
            content,
            document_type,
            project_id,
            meeting_date,
            participants,
            duration_minutes,
            meeting_id,
            metadata,
            tags,
            category,
            processing_status,
            processed_at,
            processing_error,
            created_at,
            updated_at
        )
        SELECT 
            id::uuid,
            COALESCE(title, 'Untitled Meeting'),
            COALESCE(transcript_url, storage_bucket_path, 'fireflies'),
            COALESCE(summary, ''),
            'meeting',
            project_id,
            date::date,
            participants,
            duration_minutes,
            COALESCE(fireflies_id, transcript_id),
            COALESCE(raw_metadata, '{}'::jsonb),
            tags,
            category,
            COALESCE(processing_status, 'pending'),
            processed_at,
            processing_error,
            created_at,
            updated_at
        FROM meetings
        WHERE NOT EXISTS (
            SELECT 1 FROM documents WHERE documents.id = meetings.id::uuid
        );
        
        GET DIAGNOSTICS migrated_count = ROW_COUNT;
    END IF;
    
    RETURN migrated_count;
END;
$$;

-- Function to extract insights from documents
CREATE OR REPLACE FUNCTION extract_document_insights(
    p_document_id UUID,
    p_content TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    insights_count INTEGER := 0;
BEGIN
    -- This is a placeholder for insight extraction
    -- In production, this would call an AI service to extract insights
    
    -- Example: Extract action items (simplified pattern matching)
    IF p_content ILIKE '%action:%' OR p_content ILIKE '%todo:%' OR p_content ILIKE '%task:%' THEN
        INSERT INTO ai_insights (
            document_id,
            insight_type,
            title,
            description,
            confidence_score
        ) VALUES (
            p_document_id,
            'action_item',
            'Action item detected',
            'Document contains potential action items',
            0.7
        );
        insights_count := insights_count + 1;
    END IF;
    
    RETURN insights_count;
END;
$$;

-- Trigger to update document timestamps
CREATE OR REPLACE FUNCTION update_document_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_document_timestamp();

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO CURRENT_USER;