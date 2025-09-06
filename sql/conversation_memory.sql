-- Conversation Memory Schema for RAG System
-- Provides persistent storage for conversation history, context, and extracted facts

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table: Stores conversation sessions
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,  -- Optional user identifier
    session_id TEXT NOT NULL,  -- Client-provided session identifier
    title TEXT,  -- Auto-generated conversation title
    project_id INTEGER REFERENCES projects(id),  -- Link to specific project context
    metadata JSONB DEFAULT '{}',  -- Additional conversation metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    summary TEXT,  -- Periodic summary of conversation
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted'))
);

-- Messages table: Individual messages in conversations
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens INTEGER,
    message_index INTEGER NOT NULL,  -- Order within conversation
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',  -- Store tool calls, sources, etc.
    embedding vector(1536),  -- Message embedding for similarity
    importance_score FLOAT DEFAULT 0.5,  -- For memory prioritization
    is_compressed BOOLEAN DEFAULT FALSE,  -- Whether message has been compressed
    compressed_content TEXT,  -- Compressed version for long-term storage
    retrieved_chunks JSONB,  -- IDs of chunks retrieved for this query
    UNIQUE(conversation_id, message_index)
);

-- Extracted facts/entities from conversations
CREATE TABLE IF NOT EXISTS conversation_facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE CASCADE,
    fact_type TEXT NOT NULL,  -- 'entity', 'preference', 'constraint', 'goal', 'context'
    fact_key TEXT NOT NULL,  -- e.g., 'project_name', 'deadline', 'budget'
    fact_value JSONB NOT NULL,  -- Flexible storage for different fact types
    confidence FLOAT DEFAULT 1.0,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,  -- For temporary facts
    metadata JSONB DEFAULT '{}',
    UNIQUE(conversation_id, fact_type, fact_key)  -- Prevent duplicate facts
);

-- Track which documents/chunks have been used in conversations
CREATE TABLE IF NOT EXISTS conversation_retrievals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES chunks(id),
    document_id UUID NOT NULL REFERENCES documents(id),
    relevance_score FLOAT NOT NULL,
    was_cited BOOLEAN DEFAULT FALSE,  -- Whether this chunk was cited in response
    feedback TEXT,  -- User feedback on relevance
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversation summaries for long conversations
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    message_range_start INTEGER NOT NULL,
    message_range_end INTEGER NOT NULL,
    key_points JSONB,  -- Extracted key points
    action_items JSONB,  -- Extracted action items
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    summary_embedding vector(1536)  -- For finding similar past conversations
);

-- Indexes for performance
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_conversations_last_active ON conversations(last_active DESC);
CREATE INDEX idx_conversations_project_id ON conversations(project_id) WHERE project_id IS NOT NULL;

CREATE INDEX idx_messages_conversation_id ON conversation_messages(conversation_id, message_index);
CREATE INDEX idx_messages_timestamp ON conversation_messages(timestamp DESC);
CREATE INDEX idx_messages_importance ON conversation_messages(importance_score DESC) WHERE importance_score > 0.7;
CREATE INDEX idx_messages_embedding ON conversation_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_facts_conversation_id ON conversation_facts(conversation_id);
CREATE INDEX idx_facts_type_key ON conversation_facts(fact_type, fact_key);
CREATE INDEX idx_facts_expires ON conversation_facts(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX idx_retrievals_conversation ON conversation_retrievals(conversation_id, message_id);
CREATE INDEX idx_retrievals_chunk ON conversation_retrievals(chunk_id);
CREATE INDEX idx_retrievals_cited ON conversation_retrievals(was_cited) WHERE was_cited = TRUE;

-- Function to get conversation context
CREATE OR REPLACE FUNCTION get_conversation_context(
    p_conversation_id UUID,
    p_max_messages INTEGER DEFAULT 10,
    p_min_importance FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    message_id UUID,
    role TEXT,
    content TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    importance_score FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH recent_messages AS (
        -- Get recent messages
        SELECT 
            cm.id,
            cm.role,
            CASE 
                WHEN cm.is_compressed THEN cm.compressed_content
                ELSE cm.content
            END AS content,
            cm.timestamp,
            cm.importance_score,
            cm.metadata,
            cm.message_index
        FROM conversation_messages cm
        WHERE cm.conversation_id = p_conversation_id
        ORDER BY cm.message_index DESC
        LIMIT p_max_messages * 2  -- Get more to filter by importance
    ),
    important_messages AS (
        -- Get important messages beyond the recent window
        SELECT 
            cm.id,
            cm.role,
            CASE 
                WHEN cm.is_compressed THEN cm.compressed_content
                ELSE cm.content
            END AS content,
            cm.timestamp,
            cm.importance_score,
            cm.metadata,
            cm.message_index
        FROM conversation_messages cm
        WHERE cm.conversation_id = p_conversation_id
            AND cm.importance_score >= p_min_importance
            AND cm.message_index < (
                SELECT MIN(message_index) 
                FROM recent_messages
            )
        ORDER BY cm.importance_score DESC
        LIMIT 5
    )
    SELECT 
        id AS message_id,
        role,
        content,
        timestamp,
        importance_score,
        metadata
    FROM (
        SELECT * FROM recent_messages
        WHERE importance_score >= p_min_importance OR message_index > (
            SELECT MAX(message_index) - p_max_messages
            FROM recent_messages
        )
        UNION ALL
        SELECT * FROM important_messages
    ) combined
    ORDER BY message_index;
END;
$$;

-- Function to find similar past conversations
CREATE OR REPLACE FUNCTION find_similar_conversations(
    query_embedding vector(1536),
    exclude_conversation_id UUID DEFAULT NULL,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    conversation_id UUID,
    title TEXT,
    summary TEXT,
    similarity FLOAT,
    last_active TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS conversation_id,
        c.title,
        c.summary,
        1 - (cs.summary_embedding <=> query_embedding) AS similarity,
        c.last_active
    FROM conversations c
    JOIN conversation_summaries cs ON c.id = cs.conversation_id
    WHERE cs.summary_embedding IS NOT NULL
        AND (exclude_conversation_id IS NULL OR c.id != exclude_conversation_id)
        AND c.status = 'active'
    ORDER BY cs.summary_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Trigger to update conversation updated_at
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET 
        updated_at = CURRENT_TIMESTAMP,
        last_active = CURRENT_TIMESTAMP,
        total_messages = total_messages + 1
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_on_message
    AFTER INSERT ON conversation_messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_timestamp();

-- Function to compress old messages
CREATE OR REPLACE FUNCTION compress_old_messages(
    p_conversation_id UUID,
    p_keep_recent INTEGER DEFAULT 50
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    compressed_count INTEGER := 0;
BEGIN
    -- Compress messages older than the keep_recent threshold
    WITH messages_to_compress AS (
        SELECT id, content
        FROM conversation_messages
        WHERE conversation_id = p_conversation_id
            AND is_compressed = FALSE
            AND message_index < (
                SELECT MAX(message_index) - p_keep_recent
                FROM conversation_messages
                WHERE conversation_id = p_conversation_id
            )
    )
    UPDATE conversation_messages cm
    SET 
        compressed_content = substring(mtc.content, 1, 500) || '...[compressed]',
        is_compressed = TRUE
    FROM messages_to_compress mtc
    WHERE cm.id = mtc.id;
    
    GET DIAGNOSTICS compressed_count = ROW_COUNT;
    RETURN compressed_count;
END;
$$;