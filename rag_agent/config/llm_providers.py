"""
LLM Provider Configuration for Enhanced RAG Features

This module configures various LLM providers for:
- HyDE (Hypothetical Document Embeddings) generation
- Context compression and summarization
- Conversation summarization
- Cross-encoder reranking
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio
import logging

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import cohere
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: str  # 'openai', 'anthropic', 'cohere', 'groq'
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9


class LLMProviderManager:
    """Manages multiple LLM providers for different tasks."""
    
    def __init__(self):
        # Initialize providers based on available API keys
        self.providers = {}
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.providers['openai'] = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            logger.info("OpenAI provider initialized")
        
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers['anthropic'] = AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            logger.info("Anthropic provider initialized")
        
        # Cohere (for reranking)
        if os.getenv("COHERE_API_KEY"):
            self.providers['cohere'] = cohere.Client(
                api_key=os.getenv("COHERE_API_KEY")
            )
            logger.info("Cohere provider initialized")
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            self.providers['groq'] = Groq(
                api_key=os.getenv("GROQ_API_KEY")
            )
            logger.info("Groq provider initialized")
        
        # Default configurations for different tasks
        self.task_configs = {
            'hyde': LLMConfig(
                provider='openai',
                model='gpt-4-turbo-preview',
                temperature=0.7,
                max_tokens=500
            ),
            'compression': LLMConfig(
                provider='openai',
                model='gpt-3.5-turbo',
                temperature=0.3,
                max_tokens=800
            ),
            'summarization': LLMConfig(
                provider='anthropic',
                model='claude-3-sonnet-20240229',
                temperature=0.5,
                max_tokens=1000
            ),
            'query_enhancement': LLMConfig(
                provider='openai',
                model='gpt-3.5-turbo',
                temperature=0.5,
                max_tokens=300
            )
        }
    
    async def generate_hyde(
        self,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """Generate hypothetical document for HyDE."""
        
        config = self.task_configs['hyde']
        
        prompt = f"""You are an expert assistant. Given a user's question, write a comprehensive, 
factual answer as if you had perfect knowledge. This hypothetical answer will be used 
to find similar documents in a knowledge base.

Question: {query}
"""
        
        if context:
            prompt += f"\nConversation context: {context}"
        
        prompt += "\n\nWrite a detailed, informative answer (2-3 paragraphs):"
        
        return await self._generate(prompt, config)
    
    async def compress_context(
        self,
        query: str,
        content: str,
        max_length: int = 1000
    ) -> str:
        """Compress context while preserving relevant information."""
        
        config = self.task_configs['compression']
        
        prompt = f"""Compress the following text to under {max_length} characters while preserving 
all information relevant to answering this query: "{query}"

Original text:
{content}

Compressed version (preserve key facts, entities, and relevant details):"""
        
        return await self._generate(prompt, config)
    
    async def summarize_conversation(
        self,
        messages: List[Dict[str, str]],
        max_messages: int = 50
    ) -> Dict[str, Any]:
        """Summarize a conversation for long-term memory."""
        
        config = self.task_configs['summarization']
        
        # Format messages
        conversation = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages[-max_messages:]
        ])
        
        prompt = f"""Analyze this conversation and provide a structured summary.

Conversation:
{conversation}

Provide a summary with:
1. Main topics discussed (bullet points)
2. Key decisions or conclusions reached
3. Action items or next steps identified
4. Important entities mentioned (people, projects, dates, etc.)
5. Overall sentiment and tone

Format as JSON with keys: topics, decisions, action_items, entities, sentiment"""
        
        response = await self._generate(prompt, config)
        
        # Parse JSON response
        try:
            import json
            return json.loads(response)
        except:
            return {
                "summary": response,
                "topics": [],
                "decisions": [],
                "action_items": [],
                "entities": [],
                "sentiment": "neutral"
            }
    
    async def enhance_query(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance query with expansions and sub-queries."""
        
        config = self.task_configs['query_enhancement']
        
        prompt = f"""Enhance this search query for better retrieval:

Original query: {query}
"""
        
        if conversation_context:
            prompt += f"Context: {conversation_context}\n"
        
        prompt += """
Provide:
1. An expanded version of the query with synonyms and related terms
2. 2-3 sub-queries that break down the main query
3. Key entities or concepts to search for

Format as JSON with keys: expanded_query, sub_queries, key_concepts"""
        
        response = await self._generate(prompt, config)
        
        try:
            import json
            return json.loads(response)
        except:
            return {
                "expanded_query": query,
                "sub_queries": [query],
                "key_concepts": []
            }
    
    async def rerank_with_crossencoder(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Rerank documents using Cohere's cross-encoder."""
        
        if 'cohere' not in self.providers:
            logger.warning("Cohere not available, returning original order")
            return documents[:top_k]
        
        try:
            # Prepare documents for Cohere
            docs = [doc.get('content', doc.get('text', '')) for doc in documents]
            
            # Use Cohere's rerank endpoint
            response = self.providers['cohere'].rerank(
                query=query,
                documents=docs,
                top_n=top_k,
                model='rerank-english-v2.0'
            )
            
            # Reorder documents based on Cohere's ranking
            reranked = []
            for result in response.results:
                idx = result.index
                doc = documents[idx].copy()
                doc['rerank_score'] = result.relevance_score
                reranked.append(doc)
            
            return reranked
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {e}")
            return documents[:top_k]
    
    async def _generate(self, prompt: str, config: LLMConfig) -> str:
        """Generate text using specified provider and config."""
        
        provider_name = config.provider
        
        if provider_name not in self.providers:
            # Fallback to available provider
            if 'openai' in self.providers:
                provider_name = 'openai'
            elif 'anthropic' in self.providers:
                provider_name = 'anthropic'
            else:
                logger.error(f"No LLM provider available")
                return ""
        
        try:
            if provider_name == 'openai':
                response = await self.providers['openai'].chat.completions.create(
                    model=config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p
                )
                return response.choices[0].message.content
            
            elif provider_name == 'anthropic':
                response = await self.providers['anthropic'].messages.create(
                    model=config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                return response.content[0].text
            
            elif provider_name == 'groq':
                # Groq uses sync client
                response = self.providers['groq'].chat.completions.create(
                    model=config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed with {provider_name}: {e}")
            return ""
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    def update_task_config(self, task: str, config: LLMConfig):
        """Update configuration for a specific task."""
        self.task_configs[task] = config


# Global instance
llm_manager = LLMProviderManager()


# Helper functions for easy access
async def generate_hyde(query: str, context: Optional[str] = None) -> str:
    """Generate HyDE for query."""
    return await llm_manager.generate_hyde(query, context)


async def compress_context(query: str, content: str, max_length: int = 1000) -> str:
    """Compress context for query."""
    return await llm_manager.compress_context(query, content, max_length)


async def summarize_conversation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Summarize conversation."""
    return await llm_manager.summarize_conversation(messages)


async def enhance_query(query: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Enhance query for better retrieval."""
    return await llm_manager.enhance_query(query, context)


async def rerank_documents(query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """Rerank documents using cross-encoder."""
    return await llm_manager.rerank_with_crossencoder(query, documents, top_k)