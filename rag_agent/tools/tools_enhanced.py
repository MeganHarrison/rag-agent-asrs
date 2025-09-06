"""
Enhanced RAG Tools with Memory, Reranking, Query Enhancement, and Context Compression

This module provides advanced RAG capabilities including:
1. Conversation Memory Integration
2. Reranking with cross-encoder
3. Query Enhancement with HyDE
4. Metadata Filtering
5. Context Compression
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic_ai import RunContext
from pydantic import BaseModel, Field
import asyncpg
import json
import asyncio
import logging
from datetime import datetime, timedelta
import numpy as np

from dependencies import AgentDependencies
from utils.conversation_memory import (
    ConversationMemoryManager,
    ConversationMessage,
    MessageRole
)

logger = logging.getLogger(__name__)


class EnhancedSearchResult(BaseModel):
    """Enhanced search result with additional metadata."""
    chunk_id: str
    document_id: str
    content: str
    similarity: float
    rerank_score: Optional[float] = None
    metadata: Dict[str, Any]
    document_title: str
    document_source: str
    project_id: Optional[int] = None
    was_previously_retrieved: bool = False
    compressed_content: Optional[str] = None


class QueryEnhancer:
    """Enhances queries using various techniques."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def enhance_query(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance query using multiple techniques.
        
        Returns:
            Dict containing original query, enhanced query, HyDE answer, and sub-queries
        """
        
        # Generate HyDE (Hypothetical Document Embeddings)
        hyde_answer = await self.generate_hyde(query, conversation_context)
        
        # Extract key entities and expand query
        entities = self.extract_entities(query)
        
        # Decompose into sub-queries for multi-hop reasoning
        sub_queries = await self.decompose_query(query)
        
        # Combine everything
        enhanced_query = self.combine_queries(query, hyde_answer, entities)
        
        return {
            "original": query,
            "enhanced": enhanced_query,
            "hyde": hyde_answer,
            "entities": entities,
            "sub_queries": sub_queries
        }
    
    async def generate_hyde(
        self,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """Generate a hypothetical answer for the query."""
        
        prompt = f"""Given this question, write a detailed, factual answer as if you had perfect knowledge.
This hypothetical answer will be used to find similar content.

Question: {query}
"""
        if context:
            prompt += f"\nContext from conversation: {context}"
        
        prompt += "\nHypothetical Answer:"
        
        # TODO: Call your LLM here
        # response = await self.llm.generate(prompt)
        # For now, return a simple transformation
        return f"The answer to '{query}' would likely discuss..."
    
    def extract_entities(self, query: str) -> List[str]:
        """Extract key entities from the query."""
        # Simple implementation - enhance with NER
        entities = []
        
        # Look for capitalized words (potential entities)
        words = query.split()
        for word in words:
            if word[0].isupper() and word.lower() not in ['the', 'what', 'when', 'where', 'why', 'how']:
                entities.append(word)
        
        return entities
    
    async def decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-queries."""
        
        # Simple heuristic decomposition
        sub_queries = []
        
        # Check for multi-part questions
        if ' and ' in query.lower():
            parts = query.split(' and ')
            sub_queries.extend(parts)
        
        # Check for comparison questions
        if 'compare' in query.lower() or 'difference' in query.lower():
            # Extract the items being compared
            sub_queries.append(f"What is {query.split('between')[0] if 'between' in query else query}")
        
        # Always include original
        if not sub_queries:
            sub_queries = [query]
        
        return sub_queries
    
    def combine_queries(
        self,
        original: str,
        hyde: str,
        entities: List[str]
    ) -> str:
        """Combine all query enhancements."""
        
        # Combine original with HyDE and entities
        enhanced = original
        
        if entities:
            enhanced += " " + " ".join(entities)
        
        # Add key parts from HyDE
        if hyde:
            # Take first 100 chars of HyDE to avoid over-expansion
            enhanced += " " + hyde[:100]
        
        return enhanced


class Reranker:
    """Reranks search results using various techniques."""
    
    def __init__(self, cross_encoder_model: Optional[str] = None):
        self.cross_encoder_model = cross_encoder_model
        # In production, initialize cross-encoder model here
        # self.model = CrossEncoder(cross_encoder_model)
    
    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
        diversity_lambda: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder and MMR.
        
        Args:
            query: Original query
            results: Initial search results
            top_k: Number of results to return
            diversity_lambda: Balance between relevance and diversity (0-1)
        """
        
        if not results:
            return []
        
        # Step 1: Cross-encoder reranking
        if self.cross_encoder_model:
            reranked = await self.cross_encoder_rerank(query, results)
        else:
            # Fallback to similarity scores
            reranked = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Step 2: Apply MMR for diversity
        diverse_results = self.mmr_rerank(query, reranked, diversity_lambda)
        
        # Step 3: Apply recency boost if needed
        final_results = self.apply_recency_boost(query, diverse_results)
        
        return final_results[:top_k]
    
    async def cross_encoder_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder model."""
        
        # TODO: Implement actual cross-encoder scoring
        # pairs = [[query, r['content']] for r in results]
        # scores = self.model.predict(pairs)
        
        # For now, simulate with enhanced scoring
        for result in results:
            content_lower = result['content'].lower()
            query_lower = query.lower()
            
            # Simple relevance scoring
            score = result.get('similarity', 0)
            
            # Boost for exact matches
            if query_lower in content_lower:
                score += 0.2
            
            # Boost for entity matches
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words) / len(query_words)
            score += overlap * 0.1
            
            result['rerank_score'] = min(1.0, score)
        
        return sorted(results, key=lambda x: x.get('rerank_score', 0), reverse=True)
    
    def mmr_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        lambda_param: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Maximal Marginal Relevance reranking for diversity.
        
        Args:
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
        """
        
        if not results:
            return []
        
        # Start with the most relevant document
        selected = [results[0]]
        candidates = results[1:]
        
        while candidates and len(selected) < len(results):
            mmr_scores = []
            
            for candidate in candidates:
                # Relevance to query
                relevance = candidate.get('rerank_score', candidate.get('similarity', 0))
                
                # Maximum similarity to already selected documents
                max_sim = 0
                for selected_doc in selected:
                    # Calculate similarity between documents (simplified)
                    sim = self._calculate_doc_similarity(
                        candidate['content'],
                        selected_doc['content']
                    )
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append(mmr_score)
            
            # Select document with highest MMR score
            best_idx = np.argmax(mmr_scores)
            selected.append(candidates[best_idx])
            candidates.pop(best_idx)
        
        return selected
    
    def _calculate_doc_similarity(self, doc1: str, doc2: str) -> float:
        """Calculate similarity between two documents."""
        # Simple Jaccard similarity
        words1 = set(doc1.lower().split())
        words2 = set(doc2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def apply_recency_boost(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply recency boost for time-sensitive queries."""
        
        # Check if query is temporal
        temporal_keywords = ['recent', 'latest', 'today', 'yesterday', 'last week', 'new']
        is_temporal = any(keyword in query.lower() for keyword in temporal_keywords)
        
        if not is_temporal:
            return results
        
        # Apply boost based on document age
        for result in results:
            metadata = result.get('metadata', {})
            created_at = metadata.get('created_at')
            
            if created_at:
                try:
                    doc_date = datetime.fromisoformat(created_at)
                    age_days = (datetime.now() - doc_date).days
                    
                    # Apply exponential decay boost
                    recency_boost = np.exp(-age_days / 30)  # 30-day half-life
                    
                    current_score = result.get('rerank_score', result.get('similarity', 0))
                    result['rerank_score'] = current_score * (1 + 0.3 * recency_boost)
                except:
                    pass
        
        return sorted(results, key=lambda x: x.get('rerank_score', 0), reverse=True)


class ContextCompressor:
    """Compresses retrieved context to focus on relevant parts."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    async def compress_context(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Compress context by extracting only relevant parts.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            max_length: Maximum length per chunk
        """
        
        compressed_chunks = []
        
        for chunk in chunks:
            content = chunk['content']
            
            # Extract relevant sentences
            relevant_content = await self.extract_relevant_sentences(
                query, content, max_length
            )
            
            # Create compressed version
            compressed_chunk = chunk.copy()
            compressed_chunk['compressed_content'] = relevant_content
            compressed_chunk['original_length'] = len(content)
            compressed_chunk['compressed_length'] = len(relevant_content)
            
            compressed_chunks.append(compressed_chunk)
        
        return compressed_chunks
    
    async def extract_relevant_sentences(
        self,
        query: str,
        content: str,
        max_length: int
    ) -> str:
        """Extract sentences most relevant to the query."""
        
        # Split into sentences
        sentences = self._split_sentences(content)
        
        if not sentences:
            return content[:max_length]
        
        # Score each sentence
        scored_sentences = []
        query_words = set(query.lower().split())
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            
            # Calculate relevance score
            overlap = len(query_words & sentence_words)
            score = overlap / len(query_words) if query_words else 0
            
            # Boost for exact phrase match
            if query.lower() in sentence.lower():
                score += 0.5
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Take sentences until we hit max_length
        selected = []
        current_length = 0
        
        for score, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length:
                selected.append(sentence)
                current_length += len(sentence)
            elif current_length == 0:
                # Ensure we return something
                selected.append(sentence[:max_length])
                break
        
        # Return in original order
        result = ' '.join(selected)
        
        # If we have an LLM, use it for better compression
        if self.llm and len(result) > max_length / 2:
            result = await self.llm_compress(query, result, max_length)
        
        return result
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - enhance with proper NLP
        sentences = []
        current = []
        
        for word in text.split():
            current.append(word)
            if word.endswith(('.', '!', '?')):
                sentences.append(' '.join(current))
                current = []
        
        if current:
            sentences.append(' '.join(current))
        
        return sentences
    
    async def llm_compress(
        self,
        query: str,
        content: str,
        max_length: int
    ) -> str:
        """Use LLM to compress content while preserving relevant information."""
        
        # TODO: Implement LLM-based compression
        # prompt = f"""Compress the following text to under {max_length} characters 
        # while preserving information relevant to the query: {query}
        # 
        # Text: {content}
        # 
        # Compressed:"""
        # return await self.llm.generate(prompt)
        
        # Fallback to truncation
        return content[:max_length]


async def enhanced_semantic_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    conversation_id: Optional[str] = None,
    match_count: Optional[int] = None,
    metadata_filters: Optional[Dict[str, Any]] = None,
    use_memory: bool = True,
    use_reranking: bool = True,
    use_compression: bool = True
) -> Tuple[List[EnhancedSearchResult], Dict[str, Any]]:
    """
    Enhanced semantic search with all improvements.
    
    Returns:
        Tuple of (results, search_metadata)
    """
    
    deps = ctx.deps
    
    # Initialize components
    memory_manager = ConversationMemoryManager(
        deps.db_pool,
        deps.get_embedding
    )
    query_enhancer = QueryEnhancer(None)  # Pass LLM client
    reranker = Reranker()
    compressor = ContextCompressor()
    
    search_metadata = {
        "original_query": query,
        "enhancements_used": [],
        "filters_applied": metadata_filters or {},
        "conversation_id": conversation_id
    }
    
    # Step 1: Get conversation context if available
    conversation_context = None
    if use_memory and conversation_id:
        try:
            context = await memory_manager.get_conversation_context(conversation_id)
            conversation_context = " ".join([
                msg.content for msg in context.messages[-5:]
                if msg.role == MessageRole.USER
            ])
            search_metadata["enhancements_used"].append("conversation_memory")
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
    
    # Step 2: Enhance query
    enhanced = await query_enhancer.enhance_query(query, conversation_context)
    search_query = enhanced["enhanced"]
    search_metadata["enhanced_query"] = search_query
    search_metadata["enhancements_used"].append("query_enhancement")
    
    # Step 3: Generate embeddings
    query_embedding = await deps.get_embedding(search_query)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Step 4: Apply metadata filters
    filter_clause = ""
    filter_params = []
    param_count = 3  # Starting after embedding, match_count
    
    if metadata_filters:
        conditions = []
        
        if 'project_id' in metadata_filters:
            conditions.append(f"d.metadata->>'project_id' = ${param_count}")
            filter_params.append(str(metadata_filters['project_id']))
            param_count += 1
        
        if 'date_after' in metadata_filters:
            conditions.append(f"d.created_at >= ${param_count}")
            filter_params.append(metadata_filters['date_after'])
            param_count += 1
        
        if 'document_type' in metadata_filters:
            conditions.append(f"d.metadata->>'document_type' = ${param_count}")
            filter_params.append(metadata_filters['document_type'])
            param_count += 1
        
        if conditions:
            filter_clause = "WHERE " + " AND ".join(conditions)
            search_metadata["enhancements_used"].append("metadata_filtering")
    
    # Step 5: Execute search with filters
    match_count = match_count or deps.settings.default_match_count
    
    async with deps.db_pool.acquire() as conn:
        # Get previously retrieved chunks if using memory
        previous_chunks = set()
        if use_memory and conversation_id:
            prev_results = await conn.fetch(
                """
                SELECT DISTINCT chunk_id::text
                FROM conversation_retrievals
                WHERE conversation_id = $1::uuid
                """,
                conversation_id
            )
            previous_chunks = {row['chunk_id'] for row in prev_results}
        
        # Execute main search
        query_sql = f"""
            SELECT 
                c.id::text as chunk_id,
                c.document_id::text,
                c.content,
                1 - (c.embedding <=> $1::vector) as similarity,
                c.metadata,
                d.title as document_title,
                d.source as document_source,
                d.metadata as doc_metadata
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            {filter_clause}
            ORDER BY c.embedding <=> $1::vector
            LIMIT $2
        """
        
        results = await conn.fetch(
            query_sql,
            embedding_str,
            match_count * 2,  # Get extra for reranking
            *filter_params
        )
    
    # Convert to result objects
    search_results = []
    for row in results:
        result = EnhancedSearchResult(
            chunk_id=row['chunk_id'],
            document_id=row['document_id'],
            content=row['content'],
            similarity=row['similarity'],
            metadata={
                **json.loads(row['metadata']) if row['metadata'] else {},
                **json.loads(row['doc_metadata']) if row['doc_metadata'] else {}
            },
            document_title=row['document_title'],
            document_source=row['document_source'],
            was_previously_retrieved=row['chunk_id'] in previous_chunks
        )
        search_results.append(result.dict())
    
    # Step 6: Rerank results
    if use_reranking and search_results:
        search_results = await reranker.rerank(
            query,
            search_results,
            top_k=match_count
        )
        search_metadata["enhancements_used"].append("reranking")
    
    # Step 7: Compress context
    if use_compression and search_results:
        search_results = await compressor.compress_context(
            query,
            search_results,
            max_length=1500
        )
        search_metadata["enhancements_used"].append("context_compression")
    
    # Step 8: Store retrieval in conversation memory
    if use_memory and conversation_id:
        # Store the query as a message
        message = ConversationMessage(
            role=MessageRole.USER,
            content=query,
            retrieved_chunks=[r['chunk_id'] for r in search_results[:5]]
        )
        await memory_manager.add_message(
            conversation_id,
            message,
            search_results[:5]
        )
    
    # Convert back to EnhancedSearchResult objects
    final_results = [
        EnhancedSearchResult(**result) for result in search_results[:match_count]
    ]
    
    search_metadata["results_count"] = len(final_results)
    search_metadata["total_candidates"] = len(results)
    
    return final_results, search_metadata