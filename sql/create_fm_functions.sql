-- Create function to search FM Global vectors by similarity
CREATE OR REPLACE FUNCTION match_fm_global_vectors(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    filter_asrs_topic text DEFAULT NULL,
    filter_source_type text DEFAULT NULL
) RETURNS TABLE (
    vector_id uuid,
    source_id uuid,
    source_type text,
    content text,
    similarity float,
    asrs_topic text,
    regulation_section text,
    design_parameter text,
    metadata jsonb,
    table_number text,
    figure_number text,
    reference_title text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id as vector_id,
        v.content_id as source_id,
        v.content_type as source_type,
        v.content,
        1 - (v.embedding <=> query_embedding) as similarity,
        NULL::text as asrs_topic,
        NULL::text as regulation_section,
        NULL::text as design_parameter,
        v.metadata,
        NULL::text as table_number,
        NULL::text as figure_number,
        NULL::text as reference_title
    FROM fm_global_vectors v
    WHERE (filter_source_type IS NULL OR v.content_type = filter_source_type)
    ORDER BY v.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search_fm_global(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10,
    text_weight float DEFAULT 0.3,
    filter_asrs_topic text DEFAULT NULL
) RETURNS TABLE (
    vector_id uuid,
    source_id uuid,
    source_type text,
    content text,
    combined_score float,
    asrs_topic text,
    regulation_section text,
    design_parameter text,
    metadata jsonb,
    table_number text,
    figure_number text,
    reference_title text
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT 
            v.id,
            v.content_id,
            v.content_type,
            v.content,
            1 - (v.embedding <=> query_embedding) as vector_score,
            v.metadata
        FROM fm_global_vectors v
        ORDER BY v.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    text_results AS (
        SELECT 
            v.id,
            v.content_id,
            v.content_type,
            v.content,
            ts_rank(to_tsvector('english', v.content), plainto_tsquery('english', query_text)) as text_score,
            v.metadata
        FROM fm_global_vectors v
        WHERE to_tsvector('english', v.content) @@ plainto_tsquery('english', query_text)
        LIMIT match_count * 2
    ),
    combined AS (
        SELECT 
            COALESCE(v.id, t.id) as vector_id,
            COALESCE(v.content_id, t.content_id) as source_id,
            COALESCE(v.content_type, t.content_type) as source_type,
            COALESCE(v.content, t.content) as content,
            COALESCE(v.vector_score, 0) * (1 - text_weight) + COALESCE(t.text_score, 0) * text_weight as score,
            COALESCE(v.metadata, t.metadata) as metadata
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT 
        c.vector_id,
        c.source_id,
        c.source_type,
        c.content,
        c.score as combined_score,
        NULL::text as asrs_topic,
        NULL::text as regulation_section,
        NULL::text as design_parameter,
        c.metadata,
        NULL::text as table_number,
        NULL::text as figure_number,
        NULL::text as reference_title
    FROM combined c
    ORDER BY c.score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get FM Global references by topic
CREATE OR REPLACE FUNCTION get_fm_global_references_by_topic(
    topic text,
    limit_count int DEFAULT 20
) RETURNS TABLE (
    reference_type text,
    reference_number text,
    title text,
    section text,
    asrs_relevance text
) AS $$
BEGIN
    RETURN QUERY
    (
        -- Get tables
        SELECT 
            'table'::text as reference_type,
            t.table_id as reference_number,
            t.title,
            t.asrs_type as section,
            'High'::text as asrs_relevance
        FROM fm_global_tables t
        WHERE t.title ILIKE '%' || topic || '%' 
           OR t.protection_scheme ILIKE '%' || topic || '%'
           OR t.asrs_type ILIKE '%' || topic || '%'
        LIMIT limit_count / 2
    )
    UNION ALL
    (
        -- Get figures
        SELECT 
            'figure'::text as reference_type,
            'Figure ' || f.figure_number::text as reference_number,
            f.title,
            f.figure_type as section,
            'High'::text as asrs_relevance
        FROM fm_global_figures f
        WHERE f.title ILIKE '%' || topic || '%'
           OR f.clean_caption ILIKE '%' || topic || '%'
           OR f.figure_type ILIKE '%' || topic || '%'
        LIMIT limit_count / 2
    );
END;
$$ LANGUAGE plpgsql;