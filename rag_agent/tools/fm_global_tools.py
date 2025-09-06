"""FM Global 8-34 ASRS Expert Search Tools."""

from typing import Optional, List, Dict, Any
from pydantic_ai import RunContext
from pydantic import BaseModel, Field
import asyncpg
import json
from ..core.dependencies import AgentDependencies


class FMGlobalSearchResult(BaseModel):
    """Model for FM Global search results."""
    vector_id: str
    source_id: Optional[str] = None
    source_type: str  # 'table', 'figure', 'text', 'regulation'
    content: str
    similarity: float
    asrs_topic: Optional[str] = None
    regulation_section: Optional[str] = None
    design_parameter: Optional[str] = None
    metadata: Dict[str, Any] = {}
    table_number: Optional[str] = None
    figure_number: Optional[str] = None
    reference_title: Optional[str] = None


class FMGlobalReference(BaseModel):
    """Model for FM Global table/figure references."""
    reference_type: str  # 'table' or 'figure'
    reference_number: str
    title: str
    section: Optional[str] = None
    asrs_relevance: str  # 'High', 'Medium', 'Low'


async def semantic_search_fm_global(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None,
    asrs_topic: Optional[str] = None,
    source_type: Optional[str] = None
) -> List[FMGlobalSearchResult]:
    """
    Perform semantic search on FM Global 8-34 content using vector similarity.
    
    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)
        asrs_topic: Filter by ASRS topic (fire_protection, seismic_design, etc.)
        source_type: Filter by source type (table, figure, text, regulation)
    
    Returns:
        List of FM Global search results ordered by similarity
    """
    try:
        deps = ctx.deps
        
        # Use default if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count
        
        # Validate match count
        match_count = min(match_count, deps.settings.max_match_count)
        
        # Generate embedding for query
        query_embedding = await deps.get_embedding(query)
        
        # Execute search query
        # Get database pool lazily
        db_pool = await deps.get_db_pool()
        async with db_pool.acquire() as conn:
            query_sql = """
                SELECT * FROM match_fm_global_vectors($1::vector, $2, $3, $4)
            """
            
            rows = await conn.fetch(
                query_sql,
                query_embedding,
                match_count,
                asrs_topic,
                source_type
            )
            
            # Convert results
            results = []
            for row in rows:
                result = FMGlobalSearchResult(
                    vector_id=str(row['vector_id']),
                    source_id=str(row['source_id']) if row['source_id'] else None,
                    source_type=row['source_type'],
                    content=row['content'],
                    similarity=float(row['similarity']),
                    asrs_topic=row['asrs_topic'],
                    regulation_section=row['regulation_section'],
                    design_parameter=row['design_parameter'],
                    metadata=row['metadata'] or {},
                    table_number=row['table_number'],
                    figure_number=row['figure_number'],
                    reference_title=row['reference_title']
                )
                results.append(result)
            
            return results
            
    except Exception as e:
        print(f"Semantic search error: {e}")
        return []


async def hybrid_search_fm_global(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None,
    text_weight: Optional[float] = None,
    asrs_topic: Optional[str] = None
) -> List[FMGlobalSearchResult]:
    """
    Perform hybrid search on FM Global content combining semantic and text search.
    
    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)
        text_weight: Weight for text search vs vector search (default: 0.3)
        asrs_topic: Filter by ASRS topic
    
    Returns:
        List of FM Global search results ordered by combined score
    """
    try:
        deps = ctx.deps
        
        # Use defaults if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count
        if text_weight is None:
            text_weight = deps.settings.default_text_weight
            
        # Validate parameters
        match_count = min(match_count, deps.settings.max_match_count)
        text_weight = max(0.0, min(1.0, text_weight))
        
        # Generate embedding for query
        query_embedding = await deps.get_embedding(query)
        
        # Execute hybrid search
        # Get database pool lazily
        db_pool = await deps.get_db_pool()
        async with db_pool.acquire() as conn:
            query_sql = """
                SELECT * FROM hybrid_search_fm_global($1::vector, $2, $3, $4, $5)
            """
            
            rows = await conn.fetch(
                query_sql,
                query_embedding,
                query,
                match_count,
                text_weight,
                asrs_topic
            )
            
            # Convert results
            results = []
            for row in rows:
                result = FMGlobalSearchResult(
                    vector_id=str(row['vector_id']),
                    source_id=str(row['source_id']) if row['source_id'] else None,
                    source_type=row['source_type'],
                    content=row['content'],
                    similarity=float(row['combined_score']),  # Using combined score as similarity
                    asrs_topic=row['asrs_topic'],
                    regulation_section=row['regulation_section'],
                    design_parameter=row['design_parameter'],
                    metadata=row['metadata'] or {},
                    table_number=row['table_number'],
                    figure_number=row['figure_number'],
                    reference_title=row['reference_title']
                )
                results.append(result)
            
            return results
            
    except Exception as e:
        print(f"Hybrid search error: {e}")
        return []


async def get_fm_global_references(
    ctx: RunContext[AgentDependencies],
    topic: str,
    limit_count: Optional[int] = 20
) -> List[FMGlobalReference]:
    """
    Get FM Global table and figure references for a specific ASRS topic.
    
    Args:
        ctx: Agent runtime context with dependencies
        topic: ASRS topic to search for
        limit_count: Maximum number of references to return
    
    Returns:
        List of FM Global table and figure references
    """
    try:
        deps = ctx.deps
        
        # Get database pool lazily
        db_pool = await deps.get_db_pool()
        async with db_pool.acquire() as conn:
            query_sql = """
                SELECT * FROM get_fm_global_references_by_topic($1, $2)
            """
            
            rows = await conn.fetch(query_sql, topic, limit_count)
            
            # Convert results
            results = []
            for row in rows:
                reference = FMGlobalReference(
                    reference_type=row['reference_type'],
                    reference_number=row['reference_number'],
                    title=row['title'],
                    section=row['section'],
                    asrs_relevance=row['asrs_relevance']
                )
                results.append(reference)
            
            return results
            
    except Exception as e:
        print(f"Reference search error: {e}")
        return []


async def asrs_design_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    design_focus: str,
    match_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Specialized search for ASRS design questions with comprehensive results.
    
    Args:
        ctx: Agent runtime context
        query: Design question or requirement
        design_focus: Focus area (fire_protection, seismic, structural, etc.)
        match_count: Number of results per search type
    
    Returns:
        Dictionary with semantic results, references, and design context
    """
    try:
        if match_count is None:
            match_count = 8
            
        # Perform multiple search types in parallel
        import asyncio
        
        semantic_results, references = await asyncio.gather(
            hybrid_search_fm_global(ctx, query, match_count, asrs_topic=design_focus),
            get_fm_global_references(ctx, design_focus, limit_count=10)
        )
        
        # Categorize results
        tables = [r for r in semantic_results if r.source_type == 'table']
        figures = [r for r in semantic_results if r.source_type == 'figure']
        text_content = [r for r in semantic_results if r.source_type in ['text', 'regulation']]
        
        return {
            'query': query,
            'design_focus': design_focus,
            'semantic_results': semantic_results,
            'tables_found': tables,
            'figures_found': figures,
            'text_content': text_content,
            'related_references': references,
            'total_results': len(semantic_results)
        }
        
    except Exception as e:
        print(f"ASRS design search error: {e}")
        return {
            'query': query,
            'design_focus': design_focus,
            'error': str(e),
            'semantic_results': [],
            'tables_found': [],
            'figures_found': [],
            'text_content': [],
            'related_references': [],
            'total_results': 0
        }