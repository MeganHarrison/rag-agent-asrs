-- FM Global 8-34 ASRS Expert System Database Schema
-- Specialized schema for FM Global tables, figures, and vector storage

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fm_global_vectors CASCADE;
DROP TABLE IF EXISTS fm_global_figures CASCADE;
DROP TABLE IF EXISTS fm_global_tables CASCADE;

-- Drop old indexes
DROP INDEX IF EXISTS idx_fm_global_vectors_embedding;
DROP INDEX IF EXISTS idx_fm_global_vectors_source_id;
DROP INDEX IF EXISTS idx_fm_global_tables_metadata;
DROP INDEX IF EXISTS idx_fm_global_figures_metadata;
DROP INDEX IF EXISTS idx_fm_global_vectors_content_trgm;

-- FM Global Tables - Stores structured data from FM Global 8-34 tables
CREATE TABLE fm_global_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_number TEXT NOT NULL, -- e.g., "Table 1", "Table 2-1", etc.
    title TEXT NOT NULL, -- Table title/description
    content TEXT NOT NULL, -- Table content (structured data)
    section TEXT, -- Which section of 8-34 this belongs to
    page_reference TEXT, -- Page number in 8-34
    table_type TEXT, -- e.g., "design_criteria", "spacing_requirements", "load_factors"
    metadata JSONB DEFAULT '{}', -- Additional structured data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fm_global_tables_metadata ON fm_global_tables USING GIN (metadata);
CREATE INDEX idx_fm_global_tables_number ON fm_global_tables (table_number);
CREATE INDEX idx_fm_global_tables_type ON fm_global_tables (table_type);
CREATE INDEX idx_fm_global_tables_section ON fm_global_tables (section);

-- FM Global Figures - Stores figure descriptions and references from FM Global 8-34
CREATE TABLE fm_global_figures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    figure_number TEXT NOT NULL, -- e.g., "Figure 1", "Figure 2-1", etc.
    title TEXT NOT NULL, -- Figure title/caption
    description TEXT NOT NULL, -- Detailed figure description
    section TEXT, -- Which section of 8-34 this belongs to
    page_reference TEXT, -- Page number in 8-34
    figure_type TEXT, -- e.g., "diagram", "schematic", "layout", "detail"
    asrs_component TEXT, -- e.g., "crane", "rack", "aisle", "storage_unit"
    design_context TEXT, -- e.g., "fire_protection", "seismic", "structural"
    metadata JSONB DEFAULT '{}', -- Additional structured data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fm_global_figures_metadata ON fm_global_figures USING GIN (metadata);
CREATE INDEX idx_fm_global_figures_number ON fm_global_figures (figure_number);
CREATE INDEX idx_fm_global_figures_type ON fm_global_figures (figure_type);
CREATE INDEX idx_fm_global_figures_component ON fm_global_figures (asrs_component);
CREATE INDEX idx_fm_global_figures_section ON fm_global_figures (section);

-- FM Global Vectors - Stores chunked content with embeddings for semantic search
CREATE TABLE fm_global_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID, -- References fm_global_tables.id or fm_global_figures.id
    source_type TEXT NOT NULL CHECK (source_type IN ('table', 'figure', 'text', 'regulation')),
    content TEXT NOT NULL, -- Chunk content for search
    embedding vector(1536), -- OpenAI embeddings
    chunk_index INTEGER NOT NULL,
    
    -- ASRS-specific fields
    asrs_topic TEXT, -- e.g., "fire_protection", "seismic_design", "rack_design", "crane_systems"
    regulation_section TEXT, -- Section reference in FM Global 8-34
    design_parameter TEXT, -- e.g., "spacing", "load_capacity", "clearances"
    
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fm_global_vectors_embedding ON fm_global_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_fm_global_vectors_source_id ON fm_global_vectors (source_id);
CREATE INDEX idx_fm_global_vectors_source_type ON fm_global_vectors (source_type);
CREATE INDEX idx_fm_global_vectors_topic ON fm_global_vectors (asrs_topic);
CREATE INDEX idx_fm_global_vectors_content_trgm ON fm_global_vectors USING GIN (content gin_trgm_ops);
CREATE INDEX idx_fm_global_vectors_chunk_index ON fm_global_vectors (source_id, chunk_index);

-- Enhanced search function for FM Global ASRS expertise
CREATE OR REPLACE FUNCTION match_fm_global_vectors(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    asrs_topic_filter TEXT DEFAULT NULL,
    source_type_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    vector_id UUID,
    source_id UUID,
    source_type TEXT,
    content TEXT,
    similarity FLOAT,
    asrs_topic TEXT,
    regulation_section TEXT,
    design_parameter TEXT,
    metadata JSONB,
    table_number TEXT,
    figure_number TEXT,
    reference_title TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id AS vector_id,
        v.source_id,
        v.source_type,
        v.content,
        1 - (v.embedding <=> query_embedding) AS similarity,
        v.asrs_topic,
        v.regulation_section,
        v.design_parameter,
        v.metadata,
        CASE 
            WHEN v.source_type = 'table' THEN t.table_number
            ELSE NULL
        END AS table_number,
        CASE 
            WHEN v.source_type = 'figure' THEN f.figure_number  
            ELSE NULL
        END AS figure_number,
        COALESCE(t.title, f.title, 'N/A') AS reference_title
    FROM fm_global_vectors v
    LEFT JOIN fm_global_tables t ON v.source_id = t.id AND v.source_type = 'table'
    LEFT JOIN fm_global_figures f ON v.source_id = f.id AND v.source_type = 'figure'
    WHERE v.embedding IS NOT NULL
        AND (asrs_topic_filter IS NULL OR v.asrs_topic = asrs_topic_filter)
        AND (source_type_filter IS NULL OR v.source_type = source_type_filter)
    ORDER BY v.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Hybrid search function for FM Global content
CREATE OR REPLACE FUNCTION hybrid_search_fm_global(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3,
    asrs_topic_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    vector_id UUID,
    source_id UUID,
    source_type TEXT,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    asrs_topic TEXT,
    regulation_section TEXT,
    design_parameter TEXT,
    metadata JSONB,
    table_number TEXT,
    figure_number TEXT,
    reference_title TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT 
            v.id,
            v.source_id,
            v.source_type,
            v.content,
            1 - (v.embedding <=> query_embedding) AS vector_sim,
            v.asrs_topic,
            v.regulation_section,
            v.design_parameter,
            v.metadata,
            CASE WHEN v.source_type = 'table' THEN t.table_number ELSE NULL END AS table_num,
            CASE WHEN v.source_type = 'figure' THEN f.figure_number ELSE NULL END AS figure_num,
            COALESCE(t.title, f.title, 'N/A') AS ref_title
        FROM fm_global_vectors v
        LEFT JOIN fm_global_tables t ON v.source_id = t.id AND v.source_type = 'table'
        LEFT JOIN fm_global_figures f ON v.source_id = f.id AND v.source_type = 'figure'
        WHERE v.embedding IS NOT NULL
            AND (asrs_topic_filter IS NULL OR v.asrs_topic = asrs_topic_filter)
    ),
    text_results AS (
        SELECT 
            v.id,
            v.source_id,
            v.source_type,
            v.content,
            ts_rank_cd(to_tsvector('english', v.content), plainto_tsquery('english', query_text)) AS text_sim,
            v.asrs_topic,
            v.regulation_section,
            v.design_parameter,
            v.metadata,
            CASE WHEN v.source_type = 'table' THEN t.table_number ELSE NULL END AS table_num,
            CASE WHEN v.source_type = 'figure' THEN f.figure_number ELSE NULL END AS figure_num,
            COALESCE(t.title, f.title, 'N/A') AS ref_title
        FROM fm_global_vectors v
        LEFT JOIN fm_global_tables t ON v.source_id = t.id AND v.source_type = 'table'
        LEFT JOIN fm_global_figures f ON v.source_id = f.id AND v.source_type = 'figure'
        WHERE to_tsvector('english', v.content) @@ plainto_tsquery('english', query_text)
            AND (asrs_topic_filter IS NULL OR v.asrs_topic = asrs_topic_filter)
    )
    SELECT 
        COALESCE(v.id, t.id) AS vector_id,
        COALESCE(v.source_id, t.source_id) AS source_id,
        COALESCE(v.source_type, t.source_type) AS source_type,
        COALESCE(v.content, t.content) AS content,
        (COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight)::float8 AS combined_score,
        COALESCE(v.vector_sim, 0)::float8 AS vector_similarity,
        COALESCE(t.text_sim, 0)::float8 AS text_similarity,
        COALESCE(v.asrs_topic, t.asrs_topic) AS asrs_topic,
        COALESCE(v.regulation_section, t.regulation_section) AS regulation_section,
        COALESCE(v.design_parameter, t.design_parameter) AS design_parameter,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.table_num, t.table_num) AS table_number,
        COALESCE(v.figure_num, t.figure_num) AS figure_number,
        COALESCE(v.ref_title, t.ref_title) AS reference_title
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.id = t.id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

-- Function to get related tables and figures for a specific topic
CREATE OR REPLACE FUNCTION get_fm_global_references_by_topic(
    topic TEXT,
    limit_count INT DEFAULT 20
)
RETURNS TABLE (
    reference_type TEXT,
    reference_number TEXT,
    title TEXT,
    section TEXT,
    asrs_relevance TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    (
        SELECT 
            'table'::TEXT as reference_type,
            t.table_number as reference_number,
            t.title,
            t.section,
            CASE 
                WHEN t.table_type LIKE '%' || topic || '%' THEN 'High'
                WHEN t.metadata::TEXT LIKE '%' || topic || '%' THEN 'Medium'
                ELSE 'Low'
            END as asrs_relevance
        FROM fm_global_tables t
        WHERE t.table_type LIKE '%' || topic || '%'
           OR t.metadata::TEXT LIKE '%' || topic || '%'
           OR t.content LIKE '%' || topic || '%'
        ORDER BY 
            CASE 
                WHEN t.table_type LIKE '%' || topic || '%' THEN 1
                WHEN t.metadata::TEXT LIKE '%' || topic || '%' THEN 2
                ELSE 3
            END
        LIMIT limit_count / 2
    )
    UNION ALL
    (
        SELECT 
            'figure'::TEXT as reference_type,
            f.figure_number as reference_number,
            f.title,
            f.section,
            CASE 
                WHEN f.asrs_component LIKE '%' || topic || '%' OR f.design_context LIKE '%' || topic || '%' THEN 'High'
                WHEN f.metadata::TEXT LIKE '%' || topic || '%' THEN 'Medium'
                ELSE 'Low'
            END as asrs_relevance
        FROM fm_global_figures f
        WHERE f.asrs_component LIKE '%' || topic || '%'
           OR f.design_context LIKE '%' || topic || '%'
           OR f.metadata::TEXT LIKE '%' || topic || '%'
           OR f.description LIKE '%' || topic || '%'
        ORDER BY 
            CASE 
                WHEN f.asrs_component LIKE '%' || topic || '%' OR f.design_context LIKE '%' || topic || '%' THEN 1
                WHEN f.metadata::TEXT LIKE '%' || topic || '%' THEN 2
                ELSE 3
            END
        LIMIT limit_count / 2
    );
END;
$$;

-- Update trigger for fm_global_tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_fm_global_tables_updated_at BEFORE UPDATE ON fm_global_tables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fm_global_figures_updated_at BEFORE UPDATE ON fm_global_figures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();