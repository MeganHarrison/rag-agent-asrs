"""
Intelligent Query Router for FM Global RAG System

This module analyzes queries to determine the optimal search strategy
based on query characteristics, domain-specific patterns, and historical performance.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Available search strategies."""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    HYBRID_TEXT_HEAVY = "hybrid_text_heavy"  # Higher text weight
    MULTI_STAGE = "multi_stage"  # Complex queries requiring multiple searches


class QueryType(Enum):
    """Types of queries for FM Global domain."""
    SPECIFIC_REFERENCE = "specific_reference"  # Looking for specific table/figure
    CONCEPTUAL = "conceptual"  # General understanding questions
    TECHNICAL_SPECIFICATION = "technical_spec"  # Specific measurements/requirements
    COMPLIANCE_CHECK = "compliance"  # Checking if something meets requirements
    COST_OPTIMIZATION = "cost_optimization"  # Looking for cost-saving alternatives
    COMPARISON = "comparison"  # Comparing different approaches/standards


class FMGlobalQueryRouter:
    """Routes queries to optimal search strategies for FM Global content."""
    
    def __init__(self):
        # FM Global specific terms and patterns
        self.reference_patterns = [
            r'table\s+[\d\-\.]+',
            r'figure\s+[\d\-\.]+',
            r'section\s+[\d\-\.]+',
            r'clause\s+[\d\-\.]+',
            r'appendix\s+[a-zA-Z]'
        ]
        
        self.technical_terms = {
            'sprinkler': ['k-factor', 'orifice', 'deflector', 'esfr', 'cmsa'],
            'rack': ['single-row', 'double-row', 'multi-row', 'portable'],
            'storage': ['class', 'commodity', 'plastic', 'cartoned', 'uncartoned'],
            'protection': ['wet', 'dry', 'pre-action', 'deluge', 'foam-water'],
            'asrs': ['shuttle', 'mini-load', 'crane', 'stacker'],
            'clearance': ['flue', 'transverse', 'longitudinal', 'vertical'],
            'spacing': ['maximum', 'minimum', 'standard', 'extended']
        }
        
        self.measurement_patterns = [
            r'\d+\s*(ft|feet|m|meters|in|inches)',
            r'\d+\s*(psi|bar|kpa)',
            r'\d+\s*(gpm|lpm)',
            r'\d+°[CF]',
            r'\d+\s*%'
        ]
        
        self.cost_keywords = [
            'cost', 'price', 'budget', 'economical', 'savings',
            'optimize', 'reduce', 'minimize', 'efficient', 'alternative'
        ]
        
        self.compliance_keywords = [
            'comply', 'compliant', 'meet', 'satisfy', 'requirement',
            'standard', 'code', 'regulation', 'allowed', 'permitted'
        ]
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine its characteristics.
        
        Args:
            query: The user's search query
            
        Returns:
            Dictionary with query analysis results
        """
        query_lower = query.lower()
        
        analysis = {
            'query_type': self._determine_query_type(query),
            'has_specific_reference': self._has_specific_reference(query),
            'has_measurements': bool(self._extract_measurements(query)),
            'technical_density': self._calculate_technical_density(query_lower),
            'query_length': len(query.split()),
            'extracted_references': self._extract_references(query),
            'domain_entities': self._extract_domain_entities(query_lower),
            'is_cost_focused': self._is_cost_focused(query_lower),
            'is_compliance_check': self._is_compliance_check(query_lower)
        }
        
        return analysis
    
    def route_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[SearchStrategy, Dict[str, Any]]:
        """
        Route query to optimal search strategy.
        
        Args:
            query: The search query
            context: Optional context (conversation history, user preferences)
            
        Returns:
            Tuple of (SearchStrategy, search_parameters)
        """
        analysis = self.analyze_query(query)
        
        # Route based on query characteristics
        if analysis['has_specific_reference']:
            # Specific references need high text weight for exact matching
            return SearchStrategy.HYBRID_TEXT_HEAVY, {
                'text_weight': 0.7,
                'match_count': 15,
                'filters': {'references': analysis['extracted_references']}
            }
        
        elif analysis['query_type'] == QueryType.TECHNICAL_SPECIFICATION:
            # Technical specs benefit from balanced hybrid search
            return SearchStrategy.HYBRID, {
                'text_weight': 0.5,
                'match_count': 12,
                'boost_technical': True
            }
        
        elif analysis['query_type'] == QueryType.CONCEPTUAL:
            # Conceptual queries work best with semantic search
            if analysis['query_length'] > 10:
                # Longer conceptual queries might benefit from multi-stage
                return SearchStrategy.MULTI_STAGE, {
                    'initial_count': 30,
                    'rerank_count': 10,
                    'use_query_expansion': True
                }
            else:
                return SearchStrategy.SEMANTIC, {
                    'match_count': 10,
                    'similarity_threshold': 0.7
                }
        
        elif analysis['is_cost_focused']:
            # Cost optimization queries need comprehensive results
            return SearchStrategy.MULTI_STAGE, {
                'initial_count': 25,
                'rerank_count': 15,
                'include_alternatives': True,
                'filters': {'topics': ['cost_optimization', 'alternatives']}
            }
        
        elif analysis['is_compliance_check']:
            # Compliance checks need precise matching
            return SearchStrategy.HYBRID, {
                'text_weight': 0.6,
                'match_count': 10,
                'require_high_confidence': True
            }
        
        else:
            # Default strategy based on technical density
            if analysis['technical_density'] > 0.3:
                return SearchStrategy.HYBRID, {
                    'text_weight': 0.4,
                    'match_count': 10
                }
            else:
                return SearchStrategy.SEMANTIC, {
                    'match_count': 10
                }
    
    def calculate_adaptive_text_weight(self, query: str, base_weight: float = 0.3) -> float:
        """
        Calculate adaptive text weight based on query characteristics.
        
        Args:
            query: The search query
            base_weight: Base text weight to adjust from
            
        Returns:
            Adjusted text weight (0.0 to 1.0)
        """
        weight = base_weight
        query_lower = query.lower()
        
        # Increase weight for specific references
        if self._has_specific_reference(query):
            weight += 0.4
        
        # Increase weight for exact measurements
        measurements = self._extract_measurements(query)
        if measurements:
            weight += 0.1 * min(len(measurements), 3)  # Up to 0.3 boost
        
        # Increase weight for short, specific queries
        word_count = len(query.split())
        if word_count <= 3:
            weight += 0.2
        elif word_count <= 5:
            weight += 0.1
        
        # Increase weight for queries with technical acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', query)
        if acronyms:
            weight += 0.1 * min(len(acronyms), 2)  # Up to 0.2 boost
        
        # Decrease weight for conceptual/descriptive queries
        conceptual_words = ['how', 'why', 'what', 'when', 'explain', 'describe', 'understand']
        if any(word in query_lower for word in conceptual_words):
            weight -= 0.1
        
        # Ensure weight stays within bounds
        return max(0.0, min(1.0, weight))
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query."""
        query_lower = query.lower()
        
        if self._has_specific_reference(query):
            return QueryType.SPECIFIC_REFERENCE
        elif self._is_compliance_check(query_lower):
            return QueryType.COMPLIANCE_CHECK
        elif self._is_cost_focused(query_lower):
            return QueryType.COST_OPTIMIZATION
        elif any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference']):
            return QueryType.COMPARISON
        elif self._extract_measurements(query) or self._calculate_technical_density(query_lower) > 0.4:
            return QueryType.TECHNICAL_SPECIFICATION
        else:
            return QueryType.CONCEPTUAL
    
    def _has_specific_reference(self, query: str) -> bool:
        """Check if query contains specific document references."""
        for pattern in self.reference_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _extract_references(self, query: str) -> List[str]:
        """Extract specific references from query."""
        references = []
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            references.extend(matches)
        return references
    
    def _extract_measurements(self, query: str) -> List[str]:
        """Extract measurements from query."""
        measurements = []
        for pattern in self.measurement_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            measurements.extend(matches)
        return measurements
    
    def _calculate_technical_density(self, query_lower: str) -> float:
        """Calculate the density of technical terms in the query."""
        words = query_lower.split()
        if not words:
            return 0.0
        
        technical_count = 0
        for word in words:
            for category, terms in self.technical_terms.items():
                if word in terms or any(term in word for term in terms):
                    technical_count += 1
                    break
        
        return technical_count / len(words)
    
    def _extract_domain_entities(self, query_lower: str) -> Dict[str, List[str]]:
        """Extract FM Global domain entities from query."""
        entities = {}
        
        for category, terms in self.technical_terms.items():
            found_terms = [term for term in terms if term in query_lower]
            if found_terms:
                entities[category] = found_terms
        
        return entities
    
    def _is_cost_focused(self, query_lower: str) -> bool:
        """Check if query is focused on cost optimization."""
        return any(keyword in query_lower for keyword in self.cost_keywords)
    
    def _is_compliance_check(self, query_lower: str) -> bool:
        """Check if query is checking compliance."""
        return any(keyword in query_lower for keyword in self.compliance_keywords)


# Singleton instance
query_router = FMGlobalQueryRouter()


# Convenience functions
def route_query(query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[SearchStrategy, Dict[str, Any]]:
    """Route query to optimal search strategy."""
    return query_router.route_query(query, context)


def get_adaptive_text_weight(query: str, base_weight: float = 0.3) -> float:
    """Get adaptive text weight for hybrid search."""
    return query_router.calculate_adaptive_text_weight(query, base_weight)


def analyze_query(query: str) -> Dict[str, Any]:
    """Analyze query characteristics."""
    return query_router.analyze_query(query)