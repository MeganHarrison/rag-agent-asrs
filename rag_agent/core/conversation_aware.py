"""
Conversation-Aware Retrieval for FM Global RAG System

This module provides context-aware retrieval that considers conversation history
to improve multi-turn query accuracy and relevance.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    query: str
    response: str
    timestamp: datetime
    search_results: List[str] = field(default_factory=list)  # Document IDs retrieved
    metadata: Dict[str, Any] = field(default_factory=dict)
    entities_mentioned: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Maintains conversation context for a session."""
    session_id: str
    turns: deque  # ConversationTurn objects
    active_topics: Dict[str, float]  # Topic -> relevance score
    mentioned_references: List[str]  # Tables/Figures mentioned
    current_focus: Optional[str] = None  # Current area of focus
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn and update context."""
        self.turns.append(turn)
        self.last_activity = datetime.now()
        self._update_active_topics(turn)
        self._update_references(turn)
    
    def _update_active_topics(self, turn: ConversationTurn):
        """Update active topics based on recent turn."""
        # Decay existing topic scores
        for topic in self.active_topics:
            self.active_topics[topic] *= 0.8  # Decay factor
        
        # Add new topics from entities
        for entity_type, entities in turn.entities_mentioned.items():
            for entity in entities:
                topic_key = f"{entity_type}:{entity}"
                if topic_key in self.active_topics:
                    self.active_topics[topic_key] = min(1.0, self.active_topics[topic_key] + 0.3)
                else:
                    self.active_topics[topic_key] = 0.5
        
        # Remove topics with very low relevance
        self.active_topics = {k: v for k, v in self.active_topics.items() if v > 0.1}
    
    def _update_references(self, turn: ConversationTurn):
        """Extract and store document references."""
        import re
        
        # Extract table and figure references
        tables = re.findall(r'table\s+[\d\-\.]+', turn.query + turn.response, re.IGNORECASE)
        figures = re.findall(r'figure\s+[\d\-\.]+', turn.query + turn.response, re.IGNORECASE)
        
        for ref in tables + figures:
            if ref not in self.mentioned_references:
                self.mentioned_references.append(ref)
    
    def get_recent_context(self, n_turns: int = 3) -> str:
        """Get recent conversation context as a string."""
        recent_turns = list(self.turns)[-n_turns:]
        context_parts = []
        
        for turn in recent_turns:
            context_parts.append(f"User: {turn.query}")
            if turn.response:
                # Truncate long responses
                response = turn.response[:200] + "..." if len(turn.response) > 200 else turn.response
                context_parts.append(f"Assistant: {response}")
        
        return "\n".join(context_parts)
    
    def get_active_filters(self) -> Dict[str, Any]:
        """Get search filters based on conversation context."""
        filters = {}
        
        # Add filters based on active topics
        for topic, score in self.active_topics.items():
            if score > 0.3:  # Only strong topics
                topic_type, topic_value = topic.split(':', 1)
                
                if topic_type == 'asrs_type':
                    filters.setdefault('asrs_types', []).append(topic_value)
                elif topic_type == 'container':
                    filters.setdefault('container_types', []).append(topic_value)
                elif topic_type == 'commodity':
                    filters.setdefault('commodities', []).append(topic_value)
        
        # Add mentioned references as boost factors
        if self.mentioned_references:
            filters['boost_references'] = self.mentioned_references[-5:]  # Last 5 references
        
        return filters


class ConversationAwareRetriever:
    """Retriever that considers conversation history for better results."""
    
    def __init__(self, cache_ttl_minutes: int = 30):
        self.conversation_cache: Dict[str, ConversationContext] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.entity_extractor = FMGlobalEntityExtractor()
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one."""
        # Clean expired contexts
        self._clean_expired_contexts()
        
        if session_id not in self.conversation_cache:
            self.conversation_cache[session_id] = ConversationContext(
                session_id=session_id,
                turns=deque(maxlen=10),  # Keep last 10 turns
                active_topics={},
                mentioned_references=[]
            )
        
        return self.conversation_cache[session_id]
    
    def _clean_expired_contexts(self):
        """Remove expired conversation contexts."""
        now = datetime.now()
        expired_sessions = [
            sid for sid, ctx in self.conversation_cache.items()
            if now - ctx.last_activity > self.cache_ttl
        ]
        
        for sid in expired_sessions:
            del self.conversation_cache[sid]
            logger.info(f"Expired conversation context for session {sid}")
    
    async def retrieve_with_context(
        self,
        query: str,
        session_id: str,
        base_retriever_func,
        **retriever_kwargs
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Retrieve results considering conversation context.
        
        Args:
            query: Current user query
            session_id: Session identifier
            base_retriever_func: Base retrieval function to call
            retriever_kwargs: Additional arguments for retriever
            
        Returns:
            Tuple of (results, context_metadata)
        """
        context = self.get_or_create_context(session_id)
        
        # Extract entities from current query
        entities = self.entity_extractor.extract(query)
        
        # Determine retrieval strategy based on context
        strategy = self._determine_strategy(query, context)
        
        # Modify retrieval parameters based on context
        enhanced_kwargs = self._enhance_retrieval_params(
            query, context, strategy, retriever_kwargs
        )
        
        # Add context to query if needed
        enhanced_query = self._enhance_query_with_context(query, context, strategy)
        
        # Perform retrieval
        results = await base_retriever_func(enhanced_query, **enhanced_kwargs)
        
        # Post-process results based on context
        filtered_results = self._filter_results_by_context(results, context, strategy)
        
        # Record this turn
        turn = ConversationTurn(
            query=query,
            response="",  # Will be filled later
            timestamp=datetime.now(),
            search_results=[getattr(r, 'id', str(r)) for r in filtered_results[:5]],
            metadata={'strategy': strategy},
            entities_mentioned=entities
        )
        context.add_turn(turn)
        
        # Prepare context metadata for response
        context_metadata = {
            'session_id': session_id,
            'strategy_used': strategy,
            'turns_in_context': len(context.turns),
            'active_topics': dict(context.active_topics),
            'mentioned_references': context.mentioned_references[-5:],
            'query_enhanced': enhanced_query != query,
            'filters_applied': enhanced_kwargs.get('filters', {})
        }
        
        return filtered_results, context_metadata
    
    def _determine_strategy(self, query: str, context: ConversationContext) -> str:
        """Determine retrieval strategy based on query and context."""
        query_lower = query.lower()
        
        # Check if this is a follow-up question
        if context.turns and len(query_lower.split()) < 5:
            # Short query likely refers to previous context
            if any(word in query_lower for word in ['it', 'this', 'that', 'those', 'these']):
                return 'contextual_refinement'
            
            if query_lower.startswith(('what about', 'how about', 'and for', 'what if')):
                return 'contextual_expansion'
        
        # Check if user is drilling down on a topic
        if context.active_topics and len(context.turns) > 2:
            # Check if current query relates to active topics
            for topic in context.active_topics:
                if topic.split(':')[1].lower() in query_lower:
                    return 'deep_dive'
        
        # Check if user is comparing or contrasting
        if any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference', 'better']):
            return 'comparison'
        
        # Default to standard retrieval
        return 'standard'
    
    def _enhance_retrieval_params(
        self,
        query: str,
        context: ConversationContext,
        strategy: str,
        base_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance retrieval parameters based on context."""
        params = base_params.copy()
        
        if strategy == 'contextual_refinement':
            # Increase precision for refinement queries
            params['match_count'] = params.get('match_count', 10) // 2
            params['similarity_threshold'] = params.get('similarity_threshold', 0.7) + 0.1
            
            # Add filters from context
            context_filters = context.get_active_filters()
            if context_filters:
                params.setdefault('filters', {}).update(context_filters)
        
        elif strategy == 'contextual_expansion':
            # Increase recall for expansion queries
            params['match_count'] = int(params.get('match_count', 10) * 1.5)
            params['use_query_expansion'] = True
            
        elif strategy == 'deep_dive':
            # Focus on specific topic area
            params['boost_recent'] = True  # Boost recently retrieved documents
            
            # Increase depth of retrieval
            params['match_count'] = params.get('match_count', 10) + 5
            
        elif strategy == 'comparison':
            # Retrieve more results to cover both sides
            params['match_count'] = params.get('match_count', 10) * 2
            params['diversify_results'] = True
        
        return params
    
    def _enhance_query_with_context(
        self,
        query: str,
        context: ConversationContext,
        strategy: str
    ) -> str:
        """Enhance query with conversation context."""
        if strategy == 'standard':
            return query
        
        enhanced_parts = [query]
        
        if strategy == 'contextual_refinement':
            # Add context from previous turn
            if context.turns:
                last_turn = context.turns[-1]
                # Add key entities from last query
                if last_turn.entities_mentioned:
                    context_str = "Regarding: " + ", ".join(
                        f"{v[0]}" for v in last_turn.entities_mentioned.values() if v
                    )
                    enhanced_parts.insert(0, context_str)
        
        elif strategy == 'contextual_expansion':
            # Add active topics as context
            if context.active_topics:
                top_topics = sorted(context.active_topics.items(), key=lambda x: x[1], reverse=True)[:3]
                if top_topics:
                    context_str = "Context: " + ", ".join(t[0].split(':')[1] for t in top_topics)
                    enhanced_parts.append(context_str)
        
        elif strategy == 'deep_dive':
            # Add focus area
            if context.current_focus:
                enhanced_parts.append(f"Focus: {context.current_focus}")
            
            # Add recent references
            if context.mentioned_references:
                refs = context.mentioned_references[-3:]
                enhanced_parts.append(f"Related to: {', '.join(refs)}")
        
        return " | ".join(enhanced_parts)
    
    def _filter_results_by_context(
        self,
        results: List[Any],
        context: ConversationContext,
        strategy: str
    ) -> List[Any]:
        """Filter and reorder results based on conversation context."""
        if not results or strategy == 'standard':
            return results
        
        # Score each result based on context relevance
        scored_results = []
        
        for result in results:
            score = getattr(result, 'similarity', 0.5)  # Base score
            
            # Boost if result was previously retrieved and user is drilling down
            if strategy == 'deep_dive':
                result_id = getattr(result, 'id', str(result))
                for turn in list(context.turns)[-3:]:  # Check last 3 turns
                    if result_id in turn.search_results:
                        score *= 1.2  # Boost previously seen results
                        break
            
            # Penalize if result was recently shown and strategy is expansion
            elif strategy == 'contextual_expansion':
                result_id = getattr(result, 'id', str(result))
                for turn in list(context.turns)[-2:]:  # Check last 2 turns
                    if result_id in turn.search_results:
                        score *= 0.7  # Penalize recently shown results
                        break
            
            # Boost if result contains mentioned references
            content = getattr(result, 'content', '')
            for ref in context.mentioned_references[-5:]:
                if ref.lower() in content.lower():
                    score *= 1.15
            
            scored_results.append((result, score))
        
        # Sort by adjusted score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return reordered results
        return [r[0] for r in scored_results]
    
    def update_response(self, session_id: str, response: str):
        """Update the last turn with the generated response."""
        context = self.conversation_cache.get(session_id)
        if context and context.turns:
            context.turns[-1].response = response


class FMGlobalEntityExtractor:
    """Extract FM Global specific entities from queries."""
    
    def __init__(self):
        self.entity_patterns = {
            'asrs_type': ['shuttle', 'mini-load', 'miniload', 'top-loading'],
            'container': ['closed-top', 'open-top', 'closed top', 'open top'],
            'commodity': ['plastic', 'cartoned', 'uncartoned', 'class'],
            'measurement': r'\d+\s*(?:ft|m|psi|gpm)',
            'reference': r'(?:table|figure)\s+[\d\-\.]+',
            'protection': ['wet', 'dry', 'pre-action', 'deluge', 'in-rack', 'iras']
        }
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text."""
        entities = {}
        text_lower = text.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            found = []
            
            if isinstance(patterns, list):
                # Keyword matching
                for pattern in patterns:
                    if pattern in text_lower:
                        found.append(pattern)
            else:
                # Regex matching
                import re
                matches = re.findall(patterns, text, re.IGNORECASE)
                found.extend(matches)
            
            if found:
                entities[entity_type] = found
        
        return entities


# Singleton instance
conversation_retriever = ConversationAwareRetriever()


# Convenience functions
async def retrieve_with_conversation_context(
    query: str,
    session_id: str,
    base_retriever_func,
    **kwargs
) -> Tuple[List[Any], Dict[str, Any]]:
    """Retrieve with conversation awareness."""
    return await conversation_retriever.retrieve_with_context(
        query, session_id, base_retriever_func, **kwargs
    )


def update_conversation_response(session_id: str, response: str):
    """Update conversation with generated response."""
    conversation_retriever.update_response(session_id, response)