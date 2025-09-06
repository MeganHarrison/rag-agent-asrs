-- Create fm_documents table for storing source documents
CREATE TABLE IF NOT EXISTS fm_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source_type TEXT NOT NULL, -- 'pdf', 'manual', 'standard', 'guideline', 'technical_note'
    file_path TEXT,
    url TEXT,
    document_category TEXT, -- 'fm_global_834', 'asrs_design', 'fire_protection', 'general'
    version TEXT,
    publication_date DATE,
    metadata JSONB DEFAULT '{}',
    content TEXT, -- Full document content for reference
    page_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create fm_text_chunks table for storing vectorized chunks
CREATE TABLE IF NOT EXISTS fm_text_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES fm_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    
    -- Metadata about the chunk
    page_number INTEGER,
    section_title TEXT,
    subsection_title TEXT,
    chunk_type TEXT, -- 'paragraph', 'table', 'figure_caption', 'list', 'requirement'
    
    -- FM Global specific metadata
    table_references TEXT[], -- Array of table numbers referenced in this chunk
    figure_references TEXT[], -- Array of figure numbers referenced in this chunk
    requirement_level TEXT, -- 'mandatory', 'recommended', 'optional'
    asrs_topics TEXT[], -- Topics like 'fire_protection', 'seismic', 'rack_design'
    
    -- Search optimization
    keywords TEXT[],
    search_text tsvector, -- For full-text search
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique chunks per document
    UNIQUE(document_id, chunk_index)
);

-- Create indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_fm_documents_category ON fm_documents(document_category);
CREATE INDEX IF NOT EXISTS idx_fm_documents_source_type ON fm_documents(source_type);

CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_document_id ON fm_text_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_embedding ON fm_text_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_search_text ON fm_text_chunks USING gin(search_text);
CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_asrs_topics ON fm_text_chunks USING gin(asrs_topics);
CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_table_refs ON fm_text_chunks USING gin(table_references);
CREATE INDEX IF NOT EXISTS idx_fm_text_chunks_figure_refs ON fm_text_chunks USING gin(figure_references);

-- Create function to update search_text automatically
CREATE OR REPLACE FUNCTION update_search_text()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := to_tsvector('english', 
        COALESCE(NEW.content, '') || ' ' || 
        COALESCE(NEW.section_title, '') || ' ' || 
        COALESCE(NEW.subsection_title, '') || ' ' ||
        COALESCE(array_to_string(NEW.keywords, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update search_text
DROP TRIGGER IF EXISTS update_fm_text_chunks_search_text ON fm_text_chunks;
CREATE TRIGGER update_fm_text_chunks_search_text 
    BEFORE INSERT OR UPDATE ON fm_text_chunks
    FOR EACH ROW 
    EXECUTE FUNCTION update_search_text();

-- Create unified search function that searches across all FM Global tables
CREATE OR REPLACE FUNCTION search_fm_global_unified(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10,
    search_mode text DEFAULT 'hybrid', -- 'vector', 'text', 'hybrid'
    filter_category text DEFAULT NULL,
    filter_topics text[] DEFAULT NULL
) RETURNS TABLE (
    source_id uuid,
    source_type text,
    source_table text,
    content text,
    similarity float,
    title text,
    section text,
    metadata jsonb
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- Search fm_text_chunks
    chunk_results AS (
        SELECT 
            c.id as source_id,
            'chunk'::text as source_type,
            'fm_text_chunks'::text as source_table,
            c.content,
            CASE 
                WHEN search_mode = 'vector' THEN 1 - (c.embedding <=> query_embedding)
                WHEN search_mode = 'text' THEN ts_rank(c.search_text, plainto_tsquery('english', query_text))
                ELSE (1 - (c.embedding <=> query_embedding)) * 0.7 + 
                     ts_rank(c.search_text, plainto_tsquery('english', query_text)) * 0.3
            END as similarity,
            d.title,
            c.section_title as section,
            c.metadata
        FROM fm_text_chunks c
        JOIN fm_documents d ON c.document_id = d.id
        WHERE 
            (filter_category IS NULL OR d.document_category = filter_category)
            AND (filter_topics IS NULL OR c.asrs_topics && filter_topics)
            AND (
                (search_mode = 'vector' AND c.embedding IS NOT NULL)
                OR (search_mode = 'text' AND c.search_text @@ plainto_tsquery('english', query_text))
                OR (search_mode = 'hybrid')
            )
    ),
    -- Search fm_global_vectors (existing table/figure vectors)
    vector_results AS (
        SELECT 
            v.id as source_id,
            v.content_type as source_type,
            'fm_global_vectors'::text as source_table,
            v.content,
            1 - (v.embedding <=> query_embedding) as similarity,
            COALESCE(
                (SELECT title FROM fm_global_tables WHERE id = v.content_id),
                (SELECT title FROM fm_global_figures WHERE id = v.content_id)
            ) as title,
            NULL::text as section,
            v.metadata
        FROM fm_global_vectors v
        WHERE v.embedding IS NOT NULL
    ),
    -- Combine all results
    all_results AS (
        SELECT * FROM chunk_results
        UNION ALL
        SELECT * FROM vector_results
    )
    SELECT * FROM all_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;