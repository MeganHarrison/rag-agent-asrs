"""
Enhanced FM Global 8-34 ASRS Expert Search Tools with RAG Improvements

This module integrates intelligent query routing, reranking, query expansion,
metadata pre-filtering, dynamic chunking, and conversation awareness
into the FM Global search tools.
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic_ai import RunContext
from pydantic import BaseModel, Field
import asyncpg
import json
import asyncio
import logging
from ..core.dependencies import AgentDependencies
from ..core.query_router import route_query, get_adaptive_text_weight, SearchStrategy
from ..core.rag_enhancer import (
    query_expander,
    reranker,
    embedding_enhancer,
    result_clusterer,
    EnhancedSearchResult
)
from ..core.metadata_filter import extract_metadata_filters, FilterCriteria
from ..core.conversation_aware import (
    retrieve_with_conversation_context,
    update_conversation_response
)

logger = logging.getLogger(__name__)


class FMGlobalEnhancedResult(BaseModel):
    """Enhanced FM Global search result with confidence and clustering."""
    vector_id: str
    source_id: Optional[str] = None
    source_type: str  # 'table', 'figure', 'text', 'regulation'
    content: str
    similarity: float
    rerank_score: Optional[float] = None
    confidence: float
    cluster: Optional[str] = None  # Result cluster/category
    asrs_topic: Optional[str] = None
    regulation_section: Optional[str] = None
    design_parameter: Optional[str] = None
    metadata: Dict[str, Any] = {}
    table_number: Optional[str] = None
    figure_number: Optional[str] = None
    reference_title: Optional[str] = None
    relevance_explanation: Optional[str] = None


async def intelligent_fm_global_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None,
    force_strategy: Optional[str] = None,
    use_query_expansion: bool = True,
    use_reranking: bool = True,
    return_clusters: bool = False,
    session_id: Optional[str] = None,
    use_metadata_filter: bool = True,
    use_conversation_context: bool = True
) -> Dict[str, Any]:
    """
    Intelligent FM Global search with automatic strategy selection and enhancements.
    
    This is the main entry point for enhanced FM Global searches, automatically:
    1. Routes query to optimal search strategy
    2. Expands query for better recall
    3. Executes appropriate search
    4. Reranks results for precision
    5. Clusters results by type
    
    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)
        force_strategy: Override automatic strategy selection
        use_query_expansion: Whether to expand query
        use_reranking: Whether to rerank results
        return_clusters: Whether to cluster results by type
    
    Returns:
        Dictionary with search results and metadata
    """
    try:
        deps = ctx.deps
        
        # Use default if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count
        
        # 1. Extract metadata filters for pre-filtering (NEW)
        filters = None
        if use_metadata_filter:
            filters = extract_metadata_filters(query)
            reduction = filters.estimate_reduction()
            logger.info(f"Metadata pre-filtering enabled - Estimated search space reduction: {reduction:.1%}")
        
        # 2. Apply conversation context if session provided (NEW)
        conversation_metadata = {}
        if use_conversation_context and session_id:
            # This will be integrated with the actual retrieval below
            conversation_metadata['session_id'] = session_id
            conversation_metadata['context_aware'] = True
        
        # 3. Route query to optimal strategy
        if force_strategy:
            strategy = SearchStrategy(force_strategy)
            search_params = {'match_count': match_count}
        else:
            strategy, search_params = route_query(query)
            if 'match_count' not in search_params:
                search_params['match_count'] = match_count
        
        # Add filters to search params
        if filters:
            search_params['filters'] = filters
        
        logger.info(f"Using search strategy: {strategy.value} for query: {query[:50]}...")
        
        # 2. Expand query if enabled
        query_variations = [query]
        if use_query_expansion and strategy != SearchStrategy.HYBRID_TEXT_HEAVY:
            query_variations = await query_expander.expand_query(query)
            logger.info(f"Expanded query to {len(query_variations)} variations")
        
        # 3. Execute search based on strategy
        all_results = []
        
        if strategy == SearchStrategy.MULTI_STAGE:
            # Multi-stage search with multiple passes
            all_results = await _multi_stage_search(
                ctx, query_variations, search_params, filters
            )
        elif strategy == SearchStrategy.HYBRID_TEXT_HEAVY:
            # Hybrid search with high text weight
            for q_var in query_variations[:2]:  # Limit variations for heavy text search
                results = await _hybrid_search_internal(
                    ctx, q_var, 
                    search_params.get('match_count', match_count),
                    search_params.get('text_weight', 0.7),
                    filters
                )
                all_results.extend(results)
        elif strategy == SearchStrategy.HYBRID:
            # Standard hybrid search
            text_weight = get_adaptive_text_weight(query)
            for q_var in query_variations[:3]:
                results = await _hybrid_search_internal(
                    ctx, q_var,
                    search_params.get('match_count', match_count),
                    text_weight,
                    filters
                )
                all_results.extend(results)
        else:  # SEMANTIC
            # Pure semantic search
            for q_var in query_variations:
                results = await _semantic_search_internal(
                    ctx, q_var,
                    search_params.get('match_count', match_count),
                    filters
                )
                all_results.extend(results)
        
        # Remove duplicates based on vector_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.vector_id not in seen_ids:
                seen_ids.add(result.vector_id)
                unique_results.append(result)
        
        # 4. Rerank results if enabled
        if use_reranking and unique_results:
            enhanced_results = await reranker.rerank_results(
                query, unique_results, top_k=match_count
            )
            
            # Convert to FMGlobalEnhancedResult
            final_results = []
            for enhanced in enhanced_results:
                orig = enhanced.original_result
                final_result = FMGlobalEnhancedResult(
                    vector_id=orig.vector_id,
                    source_id=orig.source_id,
                    source_type=orig.source_type,
                    content=orig.content,
                    similarity=orig.similarity,
                    rerank_score=enhanced.rerank_score,
                    confidence=enhanced.confidence,
                    asrs_topic=orig.asrs_topic,
                    regulation_section=orig.regulation_section,
                    design_parameter=orig.design_parameter,
                    metadata=orig.metadata,
                    table_number=orig.table_number,
                    figure_number=orig.figure_number,
                    reference_title=orig.reference_title,
                    relevance_explanation=enhanced.relevance_explanation
                )
                final_results.append(final_result)
        else:
            # Convert to enhanced results without reranking
            final_results = [
                FMGlobalEnhancedResult(
                    **result.dict(),
                    confidence=result.similarity,
                    rerank_score=None
                )
                for result in unique_results[:match_count]
            ]
        
        # 5. Cluster results if requested
        clusters = {}
        if return_clusters and final_results:
            clusters = result_clusterer.cluster_results(final_results)
            
            # Add cluster labels to results
            for cluster_name, cluster_results in clusters.items():
                for result in cluster_results:
                    if isinstance(result, FMGlobalEnhancedResult):
                        result.cluster = cluster_name
        
        # 6. Prepare response
        response = {
            'query': query,
            'strategy_used': strategy.value,
            'query_variations': query_variations if use_query_expansion else [query],
            'results': final_results,
            'total_results': len(final_results),
            'search_params': search_params
        }
        
        if return_clusters:
            response['clusters'] = {
                name: [r.vector_id for r in results]
                for name, results in clusters.items()
            }
        
        # Add statistics
        if final_results:
            response['statistics'] = {
                'avg_similarity': sum(r.similarity for r in final_results) / len(final_results),
                'avg_confidence': sum(r.confidence for r in final_results) / len(final_results),
                'max_confidence': max(r.confidence for r in final_results),
                'min_confidence': min(r.confidence for r in final_results)
            }
            
            if any(r.rerank_score for r in final_results):
                reranked = [r for r in final_results if r.rerank_score is not None]
                response['statistics']['avg_rerank_score'] = (
                    sum(r.rerank_score for r in reranked) / len(reranked)
                )
        
        return response
        
    except Exception as e:
        logger.error(f"Intelligent search error: {e}")
        return {
            'query': query,
            'error': str(e),
            'results': [],
            'total_results': 0
        }


async def _semantic_search_internal(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: int,
    filters: Optional[FilterCriteria] = None
) -> List[Any]:
    """Internal semantic search implementation."""
    from .fm_global_tools import FMGlobalSearchResult
    
    deps = ctx.deps
    
    # Generate embedding
    query_embedding = await deps.get_embedding(query)
    
    # Convert embedding to PostgreSQL vector string format
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Get database pool
    db_pool = await deps.get_db_pool()
    async with db_pool.acquire() as conn:
        # Build query with filters if provided
        if filters:
            where_clause, params = filters.to_sql_conditions()
            query_sql = f"""
                SELECT * FROM match_fm_global_vectors($1::vector, $2, NULL, NULL)
                WHERE vector_id IN (
                    SELECT id FROM fm_global_vectors WHERE {where_clause}
                )
            """
            rows = await conn.fetch(query_sql, embedding_str, match_count, *params)
        else:
            query_sql = """
                SELECT * FROM match_fm_global_vectors($1::vector, $2, NULL, NULL)
            """
            rows = await conn.fetch(query_sql, embedding_str, match_count)
        
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


async def _hybrid_search_internal(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: int,
    text_weight: float,
    filters: Optional[FilterCriteria] = None
) -> List[Any]:
    """Internal hybrid search implementation."""
    from .fm_global_tools import FMGlobalSearchResult
    
    deps = ctx.deps
    
    # Generate embedding
    query_embedding = await deps.get_embedding(query)
    
    # Convert embedding to PostgreSQL vector string format
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Get database pool
    db_pool = await deps.get_db_pool()
    async with db_pool.acquire() as conn:
        query_sql = """
            SELECT * FROM hybrid_search_fm_global($1::vector, $2, $3, $4, $5)
        """
        
        rows = await conn.fetch(
            query_sql,
            embedding_str,
            query,
            match_count,
            text_weight,
            filters.asrs_type[0] if filters and filters.asrs_type else None
        )
        
        results = []
        for row in rows:
            result = FMGlobalSearchResult(
                vector_id=str(row['vector_id']),
                source_id=str(row['source_id']) if row['source_id'] else None,
                source_type=row['source_type'],
                content=row['content'],
                similarity=float(row['combined_score']),
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


async def _multi_stage_search(
    ctx: RunContext[AgentDependencies],
    query_variations: List[str],
    search_params: Dict[str, Any],
    filters: Optional[FilterCriteria] = None
) -> List[Any]:
    """
    Multi-stage search implementation.
    
    Stage 1: Broad semantic search
    Stage 2: Focused hybrid search
    Stage 3: Reranking and filtering
    """
    all_results = []
    
    # Stage 1: Broad semantic search with first query
    initial_count = search_params.get('initial_count', 30)
    stage1_results = await _semantic_search_internal(
        ctx, query_variations[0], initial_count, filters
    )
    all_results.extend(stage1_results)
    
    # Stage 2: Focused hybrid search with variations
    for q_var in query_variations[1:3]:  # Use 2-3 variations
        hybrid_results = await _hybrid_search_internal(
            ctx, q_var, 
            initial_count // 2,
            0.5,  # Balanced weight for multi-stage
            filters
        )
        all_results.extend(hybrid_results)
    
    return all_results


async def create_contextual_fm_global_embedding(
    ctx: RunContext[AgentDependencies],
    chunk_content: str,
    chunk_metadata: Dict[str, Any],
    prev_chunk_content: Optional[str] = None,
    next_chunk_content: Optional[str] = None
) -> List[float]:
    """
    Create contextual embedding for FM Global content.
    
    Args:
        ctx: Agent runtime context
        chunk_content: Main chunk content
        chunk_metadata: Chunk metadata (table_number, figure_number, etc.)
        prev_chunk_content: Previous chunk content
        next_chunk_content: Next chunk content
    
    Returns:
        Embedding vector with contextual information
    """
    deps = ctx.deps
    
    # Create enhanced content with context
    enhanced_content = await embedding_enhancer.create_contextual_embedding(
        chunk_content,
        prev_chunk_content,
        next_chunk_content,
        chunk_metadata
    )
    
    # Generate embedding for enhanced content
    embedding = await deps.get_embedding(enhanced_content)
    
    return embedding


async def analyze_fm_global_query_intent(
    ctx: RunContext[AgentDependencies],
    query: str
) -> Dict[str, Any]:
    """
    Analyze the intent and characteristics of an FM Global query.
    
    Args:
        ctx: Agent runtime context
        query: User query
    
    Returns:
        Dictionary with query analysis including intent, entities, and recommendations
    """
    from ..core.query_router import query_router
    
    # Get query analysis
    analysis = query_router.analyze_query(query)
    
    # Get recommended search strategy
    strategy, params = route_query(query)
    
    # Get adaptive text weight
    text_weight = get_adaptive_text_weight(query)
    
    return {
        'query': query,
        'analysis': analysis,
        'recommended_strategy': strategy.value,
        'recommended_params': params,
        'adaptive_text_weight': text_weight,
        'query_type': analysis['query_type'].value if hasattr(analysis['query_type'], 'value') else str(analysis['query_type']),
        'has_specific_reference': analysis['has_specific_reference'],
        'technical_density': analysis['technical_density'],
        'domain_entities': analysis['domain_entities']
    }