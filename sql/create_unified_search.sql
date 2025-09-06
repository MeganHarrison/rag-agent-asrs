-- Create unified search function that searches across ALL FM Global tables
CREATE OR REPLACE FUNCTION search_fm_global_all(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10
) RETURNS TABLE (
    source_id text,
    source_type text,
    source_table text,
    content text,
    similarity float,
    title text,
    metadata jsonb
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- Search fm_text_chunks (document chunks with embeddings)
    chunk_results AS (
        SELECT 
            c.id::text as source_id,
            c.content_type as source_type,
            'fm_text_chunks'::text as source_table,
            c.raw_text as content,
            1 - (c.embedding <=> query_embedding) as similarity,
            COALESCE(c.chunk_summary, CONCAT('Chunk from ', c.doc_id)) as title,
            jsonb_build_object(
                'doc_id', c.doc_id,
                'page_number', c.page_number,
                'section_path', c.section_path,
                'related_tables', c.related_tables,
                'related_figures', c.related_figures,
                'topics', c.topics
            ) as metadata
        FROM fm_text_chunks c
        WHERE c.embedding IS NOT NULL
    ),
    
    -- Search fm_table_vectors (table embeddings)
    table_results AS (
        SELECT 
            tv.id::text as source_id,
            tv.content_type as source_type,
            'fm_table_vectors'::text as source_table,
            tv.content_text as content,
            1 - (tv.embedding <=> query_embedding) as similarity,
            CONCAT('Table ', tv.table_id) as title,
            tv.metadata
        FROM fm_table_vectors tv
        WHERE tv.embedding IS NOT NULL
    ),
    
    -- Search fm_global_vectors (if it has data)
    vector_results AS (
        SELECT 
            v.id::text as source_id,
            v.content_type as source_type,
            'fm_global_vectors'::text as source_table,
            v.content,
            1 - (v.embedding <=> query_embedding) as similarity,
            'FM Global Vector' as title,
            v.metadata
        FROM fm_global_vectors v
        WHERE v.embedding IS NOT NULL
    ),
    
    -- Combine all results
    all_results AS (
        SELECT * FROM chunk_results
        UNION ALL
        SELECT * FROM table_results
        UNION ALL
        SELECT * FROM vector_results
    )
    
    SELECT * FROM all_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create a text search function for fm_text_chunks
CREATE OR REPLACE FUNCTION text_search_chunks(
    search_query text,
    match_count int DEFAULT 10
) RETURNS TABLE (
    chunk_id uuid,
    doc_id text,
    content text,
    chunk_summary text,
    page_number int,
    section_path text[],
    related_tables text[],
    related_figures text[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id as chunk_id,
        c.doc_id,
        c.raw_text as content,
        c.chunk_summary,
        c.page_number,
        c.section_path,
        c.related_tables,
        c.related_figures
    FROM fm_text_chunks c
    WHERE 
        c.raw_text ILIKE '%' || search_query || '%'
        OR c.chunk_summary ILIKE '%' || search_query || '%'
        OR search_query = ANY(c.search_keywords)
        OR search_query = ANY(c.topics)
    ORDER BY 
        CASE 
            WHEN c.chunk_summary ILIKE '%' || search_query || '%' THEN 1
            WHEN c.raw_text ILIKE '%' || search_query || '%' THEN 2
            ELSE 3
        END
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;