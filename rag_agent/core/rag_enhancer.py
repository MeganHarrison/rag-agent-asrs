"""
RAG Enhancement Module for FM Global System

Provides reranking, query expansion, and other advanced RAG capabilities
specifically tuned for FM Global 8-34 ASRS content.
"""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSearchResult:
    """Enhanced search result with reranking score."""
    original_result: Any  # Original search result
    rerank_score: float
    confidence: float
    relevance_explanation: Optional[str] = None


class FMGlobalQueryExpander:
    """Expands queries with FM Global domain knowledge."""
    
    def __init__(self):
        # Domain-specific expansions
        self.acronym_expansions = {
            'asrs': 'automated storage retrieval system',
            'esfr': 'early suppression fast response',
            'cmsa': 'control mode specific application',
            'iras': 'in-rack sprinkler',
            'rdd': 'rack depth dimension',
            'fmg': 'fm global',
            'vfc': 'vertical flue clearance',
            'hfc': 'horizontal flue clearance'
        }
        
        self.synonym_mappings = {
            'sprinkler': ['sprinkler head', 'spray nozzle', 'fire suppression'],
            'rack': ['storage rack', 'pallet rack', 'shelving'],
            'clearance': ['spacing', 'distance', 'gap', 'separation'],
            'commodity': ['material', 'product', 'goods', 'inventory'],
            'protection': ['fire protection', 'suppression', 'safety system'],
            'wet system': ['wet pipe', 'water-filled pipe'],
            'dry system': ['dry pipe', 'air-filled pipe'],
            'shuttle': ['shuttle system', 'shuttle asrs', 'horizontal shuttle'],
            'mini-load': ['miniload', 'mini load asrs', 'tote storage']
        }
        
        self.contextual_expansions = {
            'cost': ['price', 'budget', 'expense', 'investment'],
            'optimize': ['improve', 'enhance', 'maximize efficiency', 'reduce cost'],
            'comply': ['meet requirements', 'satisfy standards', 'follow guidelines'],
            'design': ['layout', 'configuration', 'arrangement', 'setup'],
            'calculate': ['determine', 'compute', 'figure out', 'estimate']
        }
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Expand query with multiple variations.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations including original
        """
        variations = [query]  # Always include original
        query_lower = query.lower()
        
        # 1. Expand acronyms
        acronym_expanded = self._expand_acronyms(query_lower)
        if acronym_expanded != query_lower:
            variations.append(acronym_expanded)
        
        # 2. Add synonyms
        synonym_variations = self._generate_synonym_variations(query_lower)
        variations.extend(synonym_variations[:2])  # Limit to avoid explosion
        
        # 3. Add FM Global specific context
        fm_context_query = self._add_fm_context(query)
        if fm_context_query != query:
            variations.append(fm_context_query)
        
        # 4. Generate focused sub-queries for complex queries
        if len(query.split()) > 8:
            sub_queries = self._generate_sub_queries(query)
            variations.extend(sub_queries[:2])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_variations.append(v)
        
        return unique_variations[:5]  # Limit total variations
    
    def _expand_acronyms(self, query: str) -> str:
        """Expand known acronyms in query."""
        expanded = query
        for acronym, expansion in self.acronym_expansions.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(acronym) + r'\b'
            expanded = re.sub(pattern, f"{acronym} {expansion}", expanded, flags=re.IGNORECASE)
        return expanded
    
    def _generate_synonym_variations(self, query: str) -> List[str]:
        """Generate query variations using synonyms."""
        variations = []
        
        for term, synonyms in self.synonym_mappings.items():
            if term in query:
                # Create variation with first synonym
                variation = query.replace(term, synonyms[0])
                if variation != query:
                    variations.append(variation)
        
        return variations
    
    def _add_fm_context(self, query: str) -> str:
        """Add FM Global specific context to query."""
        # Check if query lacks specific FM context
        if not any(term in query.lower() for term in ['fm global', 'fm 8-34', 'fmg']):
            # Add context for certain query types
            if any(term in query.lower() for term in ['requirement', 'standard', 'code']):
                return f"FM Global 8-34 {query}"
            elif any(term in query.lower() for term in ['sprinkler', 'protection', 'asrs']):
                return f"{query} FM Global requirements"
        
        return query
    
    def _generate_sub_queries(self, query: str) -> List[str]:
        """Break complex queries into focused sub-queries."""
        sub_queries = []
        
        # Extract key phrases
        if 'and' in query.lower():
            parts = query.split(' and ')
            sub_queries.extend(parts)
        
        # Extract questions within the query
        question_words = ['what', 'how', 'when', 'where', 'which', 'why']
        for word in question_words:
            if word in query.lower():
                # Extract the question part
                pattern = f"{word}[^.?!]*[.?!]?"
                matches = re.findall(pattern, query, re.IGNORECASE)
                sub_queries.extend(matches)
                break
        
        return sub_queries


class FMGlobalReranker:
    """Reranks search results for FM Global domain."""
    
    def __init__(self):
        self.domain_boost_terms = {
            'table': 2.0,
            'figure': 2.0,
            'section': 1.5,
            'requirement': 1.5,
            'shall': 1.3,
            'must': 1.3,
            'minimum': 1.2,
            'maximum': 1.2
        }
        
        self.penalty_terms = {
            'draft': 0.5,
            'obsolete': 0.3,
            'superseded': 0.3,
            'example': 0.8  # Unless specifically asked for
        }
    
    async def rerank_results(
        self,
        query: str,
        results: List[Any],
        top_k: Optional[int] = None
    ) -> List[EnhancedSearchResult]:
        """
        Rerank search results based on relevance to query.
        
        Args:
            query: Original search query
            results: List of search results to rerank
            top_k: Number of top results to return
            
        Returns:
            List of reranked results with scores
        """
        if not results:
            return []
        
        # Calculate reranking scores
        enhanced_results = []
        for result in results:
            score = await self._calculate_rerank_score(query, result)
            confidence = self._calculate_confidence(query, result, score)
            
            enhanced = EnhancedSearchResult(
                original_result=result,
                rerank_score=score,
                confidence=confidence
            )
            enhanced_results.append(enhanced)
        
        # Sort by rerank score
        enhanced_results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # Apply top_k if specified
        if top_k:
            enhanced_results = enhanced_results[:top_k]
        
        return enhanced_results
    
    async def _calculate_rerank_score(self, query: str, result: Any) -> float:
        """Calculate reranking score for a result."""
        # Start with original similarity score if available
        base_score = getattr(result, 'similarity', 0.5)
        
        # Get content
        content = getattr(result, 'content', '')
        content_lower = content.lower()
        query_lower = query.lower()
        
        # 1. Exact match boost
        if query_lower in content_lower:
            base_score *= 1.5
        
        # 2. Term overlap score
        query_terms = set(query_lower.split())
        content_terms = set(content_lower.split())
        overlap = len(query_terms & content_terms)
        if query_terms:
            overlap_ratio = overlap / len(query_terms)
            base_score *= (1 + overlap_ratio * 0.5)
        
        # 3. Domain-specific boosts
        for term, boost in self.domain_boost_terms.items():
            if term in content_lower:
                base_score *= boost
        
        # 4. Apply penalties
        for term, penalty in self.penalty_terms.items():
            if term in content_lower:
                base_score *= penalty
        
        # 5. Reference matching boost
        references = re.findall(r'(table|figure)\s+[\d\-\.]+', query_lower)
        for ref in references:
            if ref in content_lower:
                base_score *= 2.0  # Strong boost for exact reference match
        
        # 6. Metadata boost (if available)
        metadata = getattr(result, 'metadata', {})
        if metadata:
            # Boost for matching ASRS type
            if 'asrs_type' in metadata:
                if metadata['asrs_type'].lower() in query_lower:
                    base_score *= 1.3
            
            # Boost for matching commodity type
            if 'commodity_type' in metadata:
                if metadata['commodity_type'].lower() in query_lower:
                    base_score *= 1.2
        
        # Normalize score to [0, 1]
        return min(1.0, base_score)
    
    def _calculate_confidence(self, query: str, result: Any, rerank_score: float) -> float:
        """Calculate confidence score for the result."""
        confidence = rerank_score
        
        # Boost confidence for specific indicators
        content = getattr(result, 'content', '').lower()
        
        # High confidence indicators
        if 'shall' in content or 'must' in content:
            confidence = min(1.0, confidence + 0.1)
        
        # Check for specific references
        if re.search(r'table\s+[\d\-\.]+', content, re.IGNORECASE):
            confidence = min(1.0, confidence + 0.05)
        
        # Lower confidence for uncertain language
        uncertain_terms = ['may', 'might', 'could', 'possibly', 'generally']
        if any(term in content for term in uncertain_terms):
            confidence *= 0.9
        
        return confidence


class ContextualEmbeddingEnhancer:
    """Enhances embeddings with contextual information."""
    
    def __init__(self):
        self.context_window = 200  # Characters for context
    
    async def create_contextual_embedding(
        self,
        chunk_content: str,
        prev_chunk: Optional[str] = None,
        next_chunk: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create enhanced content for embedding with context.
        
        Args:
            chunk_content: Main chunk content
            prev_chunk: Previous chunk content
            next_chunk: Next chunk content
            metadata: Chunk metadata
            
        Returns:
            Enhanced content string for embedding
        """
        parts = []
        
        # Add metadata context if available
        if metadata:
            if 'title' in metadata:
                parts.append(f"Document: {metadata['title']}")
            if 'section' in metadata:
                parts.append(f"Section: {metadata['section']}")
            if 'table_number' in metadata:
                parts.append(f"Table {metadata['table_number']}")
            if 'figure_number' in metadata:
                parts.append(f"Figure {metadata['figure_number']}")
        
        # Add surrounding context
        if prev_chunk:
            # Get last N characters of previous chunk
            context_start = max(0, len(prev_chunk) - self.context_window)
            parts.append(f"Previous context: ...{prev_chunk[context_start:]}")
        
        # Add main content
        parts.append(f"Content: {chunk_content}")
        
        if next_chunk:
            # Get first N characters of next chunk
            context_end = min(len(next_chunk), self.context_window)
            parts.append(f"Following context: {next_chunk[:context_end]}...")
        
        return "\n".join(parts)


class ResultClustering:
    """Clusters search results by topic/type."""
    
    def cluster_results(self, results: List[Any]) -> Dict[str, List[Any]]:
        """
        Cluster results into categories.
        
        Args:
            results: List of search results
            
        Returns:
            Dictionary of clustered results
        """
        clusters = {
            'tables': [],
            'figures': [],
            'requirements': [],
            'specifications': [],
            'procedures': [],
            'general': []
        }
        
        for result in results:
            content = getattr(result, 'content', '').lower()
            metadata = getattr(result, 'metadata', {})
            
            # Categorize based on content and metadata
            if 'table' in content or 'table_number' in metadata:
                clusters['tables'].append(result)
            elif 'figure' in content or 'figure_number' in metadata:
                clusters['figures'].append(result)
            elif any(term in content for term in ['shall', 'must', 'requirement']):
                clusters['requirements'].append(result)
            elif any(term in content for term in ['specification', 'parameter', 'dimension']):
                clusters['specifications'].append(result)
            elif any(term in content for term in ['procedure', 'step', 'process']):
                clusters['procedures'].append(result)
            else:
                clusters['general'].append(result)
        
        # Remove empty clusters
        return {k: v for k, v in clusters.items() if v}


# Singleton instances
query_expander = FMGlobalQueryExpander()
reranker = FMGlobalReranker()
embedding_enhancer = ContextualEmbeddingEnhancer()
result_clusterer = ResultClustering()