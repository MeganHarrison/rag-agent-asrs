-- Fix FM Global search functions to match actual database schema

-- Drop existing functions
DROP FUNCTION IF EXISTS match_fm_global_vectors(vector, int, text, text);
DROP FUNCTION IF EXISTS hybrid_search_fm_global(vector, text, int, float, text);

-- Create corrected search function
CREATE OR REPLACE FUNCTION match_fm_global_vectors(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    filter_asrs_type text DEFAULT NULL,
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
    WITH vector_search AS (
        SELECT 
            v.id as vector_id,
            v.content_id as source_id,
            v.content_type as source_type,
            v.content,
            1 - (v.embedding <=> query_embedding) as similarity,
            v.metadata,
            CASE 
                WHEN v.content_type = 'table' THEN t.asrs_type
                WHEN v.content_type = 'figure' THEN f.asrs_type
                ELSE NULL
            END as asrs_topic,
            CASE 
                WHEN v.content_type = 'table' THEN t.table_id
                WHEN v.content_type = 'figure' THEN 'Figure ' || f.figure_number::text
                ELSE NULL
            END as reference_number,
            CASE 
                WHEN v.content_type = 'table' THEN t.title
                WHEN v.content_type = 'figure' THEN f.title
                ELSE NULL
            END as reference_title
        FROM fm_global_vectors v
        LEFT JOIN fm_global_tables t ON v.content_id = t.id AND v.content_type = 'table'
        LEFT JOIN fm_global_figures f ON v.content_id = f.id AND v.content_type = 'figure'
        WHERE 
            (filter_source_type IS NULL OR v.content_type = filter_source_type)
            AND (filter_asrs_type IS NULL OR 
                 (v.content_type = 'table' AND t.asrs_type = filter_asrs_type) OR
                 (v.content_type = 'figure' AND f.asrs_type = filter_asrs_type))
        ORDER BY v.embedding <=> query_embedding
        LIMIT match_count
    )
    SELECT 
        vs.vector_id,
        vs.source_id,
        vs.source_type,
        vs.content,
        vs.similarity,
        vs.asrs_topic,
        NULL::text as regulation_section,
        NULL::text as design_parameter,
        vs.metadata,
        CASE WHEN vs.source_type = 'table' THEN vs.reference_number ELSE NULL END as table_number,
        CASE WHEN vs.source_type = 'figure' THEN vs.reference_number ELSE NULL END as figure_number,
        vs.reference_title
    FROM vector_search vs;
END;
$$ LANGUAGE plpgsql;

-- Create corrected hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search_fm_global(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10,
    text_weight float DEFAULT 0.3,
    filter_asrs_type text DEFAULT NULL
) RETURNS TABLE (
    vector_id uuid,
    source_id uuid,
    source_type text,
    content text,
    combined_score float,
    vector_similarity float,
    text_similarity float,
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
            v.metadata,
            CASE 
                WHEN v.content_type = 'table' THEN t.asrs_type
                WHEN v.content_type = 'figure' THEN f.asrs_type
                ELSE NULL
            END as asrs_type_val,
            CASE 
                WHEN v.content_type = 'table' THEN t.table_id
                WHEN v.content_type = 'figure' THEN 'Figure ' || f.figure_number::text
                ELSE NULL
            END as reference_number,
            CASE 
                WHEN v.content_type = 'table' THEN t.title
                WHEN v.content_type = 'figure' THEN f.title
                ELSE NULL
            END as reference_title
        FROM fm_global_vectors v
        LEFT JOIN fm_global_tables t ON v.content_id = t.id AND v.content_type = 'table'
        LEFT JOIN fm_global_figures f ON v.content_id = f.id AND v.content_type = 'figure'
        WHERE 
            (filter_asrs_type IS NULL OR 
             (v.content_type = 'table' AND t.asrs_type = filter_asrs_type) OR
             (v.content_type = 'figure' AND f.asrs_type = filter_asrs_type))
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
            v.metadata,
            CASE 
                WHEN v.content_type = 'table' THEN t.asrs_type
                WHEN v.content_type = 'figure' THEN f.asrs_type
                ELSE NULL
            END as asrs_type_val,
            CASE 
                WHEN v.content_type = 'table' THEN t.table_id
                WHEN v.content_type = 'figure' THEN 'Figure ' || f.figure_number::text
                ELSE NULL
            END as reference_number,
            CASE 
                WHEN v.content_type = 'table' THEN t.title
                WHEN v.content_type = 'figure' THEN f.title
                ELSE NULL
            END as reference_title
        FROM fm_global_vectors v
        LEFT JOIN fm_global_tables t ON v.content_id = t.id AND v.content_type = 'table'
        LEFT JOIN fm_global_figures f ON v.content_id = f.id AND v.content_type = 'figure'
        WHERE 
            to_tsvector('english', v.content) @@ plainto_tsquery('english', query_text)
            AND (filter_asrs_type IS NULL OR 
                 (v.content_type = 'table' AND t.asrs_type = filter_asrs_type) OR
                 (v.content_type = 'figure' AND f.asrs_type = filter_asrs_type))
        LIMIT match_count * 2
    ),
    combined AS (
        SELECT 
            COALESCE(v.id, t.id) as vector_id,
            COALESCE(v.content_id, t.content_id) as source_id,
            COALESCE(v.content_type, t.content_type) as source_type,
            COALESCE(v.content, t.content) as content,
            COALESCE(v.vector_score, 0) * (1 - text_weight) + COALESCE(t.text_score, 0) * text_weight as score,
            COALESCE(v.vector_score, 0) as vector_similarity,
            COALESCE(t.text_score, 0) as text_similarity,
            COALESCE(v.metadata, t.metadata) as metadata,
            COALESCE(v.asrs_type_val, t.asrs_type_val) as asrs_topic,
            COALESCE(v.reference_number, t.reference_number) as reference_number,
            COALESCE(v.reference_title, t.reference_title) as reference_title,
            COALESCE(v.content_type, t.content_type) as content_type_final
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT 
        c.vector_id,
        c.source_id,
        c.source_type,
        c.content,
        c.score as combined_score,
        c.vector_similarity,
        c.text_similarity,
        c.asrs_topic,
        NULL::text as regulation_section,
        NULL::text as design_parameter,
        c.metadata,
        CASE WHEN c.content_type_final = 'table' THEN c.reference_number ELSE NULL END as table_number,
        CASE WHEN c.content_type_final = 'figure' THEN c.reference_number ELSE NULL END as figure_number,
        c.reference_title
    FROM combined c
    ORDER BY c.score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION match_fm_global_vectors(vector, int, text, text) TO CURRENT_USER;
GRANT EXECUTE ON FUNCTION hybrid_search_fm_global(vector, text, int, float, text) TO CURRENT_USER;