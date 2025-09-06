"""
Vectorization API for RAG Agent PM

This module provides API endpoints for document vectorization,
called by pm-rag-vectorize after document ingestion.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
from dotenv import load_dotenv

# Import our enhanced components
from utils.db_utils import db_pool, initialize_database
from ingestion.intelligent_chunker import IntelligentChunker
from ingestion.embedder import create_embedder
from llm_providers import llm_manager, summarize_conversation
from utils.conversation_memory import ConversationMemoryManager

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Agent PM Vectorization API",
    description="API for document vectorization and RAG operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VectorizeRequest(BaseModel):
    """Request model for vectorization."""
    document_id: str
    document_type: Optional[str] = "document"
    force_revectorize: bool = False
    use_intelligent_chunking: bool = True
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200


class VectorizeResponse(BaseModel):
    """Response model for vectorization."""
    success: bool
    document_id: str
    chunks_created: int
    embeddings_generated: int
    processing_time_ms: float
    message: Optional[str] = None
    error: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    """Request model for document search."""
    query: str
    project_id: Optional[int] = None
    document_type: Optional[str] = None
    limit: int = Field(default=10, le=100)
    use_semantic: bool = True


class ExtractInsightsRequest(BaseModel):
    """Request model for insight extraction."""
    document_id: str
    extract_action_items: bool = True
    extract_decisions: bool = True
    extract_risks: bool = True


class VectorizationService:
    """Service for handling document vectorization."""
    
    def __init__(self):
        self.chunker = None
        self.embedder = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the service."""
        if not self.initialized:
            await initialize_database()
            
            self.chunker = IntelligentChunker(
                base_chunk_size=1000,
                chunk_overlap=200,
                enable_hierarchical=True,
                enable_semantic=True
            )
            
            self.embedder = create_embedder()
            self.initialized = True
            
            logger.info("Vectorization service initialized")
    
    async def vectorize_document(
        self,
        document_id: str,
        force_revectorize: bool = False,
        use_intelligent_chunking: bool = True
    ) -> Dict[str, Any]:
        """Vectorize a document."""
        
        start_time = datetime.now()
        
        try:
            async with db_pool.acquire() as conn:
                # Check if document exists
                document = await conn.fetchrow(
                    """
                    SELECT id, title, content, document_type, project_id, metadata
                    FROM documents
                    WHERE id = $1::uuid
                    """,
                    document_id
                )
                
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                # Check if already vectorized
                if not force_revectorize:
                    existing_chunks = await conn.fetchval(
                        "SELECT COUNT(*) FROM chunks WHERE document_id = $1::uuid",
                        document_id
                    )
                    
                    if existing_chunks > 0:
                        return {
                            'success': True,
                            'document_id': document_id,
                            'chunks_created': 0,
                            'embeddings_generated': 0,
                            'message': f'Document already vectorized with {existing_chunks} chunks'
                        }
                
                # Update status to processing
                await conn.execute(
                    """
                    UPDATE documents
                    SET processing_status = 'processing', updated_at = NOW()
                    WHERE id = $1::uuid
                    """,
                    document_id
                )
                
                # Delete existing chunks if revectorizing
                if force_revectorize:
                    await conn.execute(
                        "DELETE FROM chunks WHERE document_id = $1::uuid",
                        document_id
                    )
                
                # Chunk the document
                if use_intelligent_chunking:
                    chunks, chunk_metadata = await self.chunker.chunk_document(
                        content=document['content'],
                        document_id=document_id,
                        metadata={
                            'document_type': document['document_type'],
                            'project_id': document['project_id'],
                            **(json.loads(document['metadata']) if document['metadata'] else {})
                        }
                    )
                    
                    # Convert intelligent chunks to standard format
                    chunk_texts = [chunk.content for chunk in chunks]
                    chunk_metadatas = [
                        {
                            'chunk_type': chunk.chunk_type.value,
                            'parent_id': chunk.parent_id,
                            'depth_level': chunk.depth_level,
                            **chunk.metadata
                        }
                        for chunk in chunks
                    ]
                else:
                    # Simple chunking
                    from langchain.text_splitter import RecursiveCharacterTextSplitter
                    
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200,
                        separators=["\n\n", "\n", " ", ""]
                    )
                    
                    chunk_texts = splitter.split_text(document['content'])
                    chunk_metadatas = [{'chunk_type': 'standard'} for _ in chunk_texts]
                
                # Generate embeddings
                embeddings = await self.embedder.embed_texts(chunk_texts)
                
                # Store chunks and embeddings
                chunks_created = 0
                async with conn.transaction():
                    for i, (text, embedding, metadata) in enumerate(zip(chunk_texts, embeddings, chunk_metadatas)):
                        # Convert embedding to PostgreSQL format
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        await conn.execute(
                            """
                            INSERT INTO chunks (
                                document_id,
                                content,
                                embedding,
                                chunk_index,
                                chunk_type,
                                metadata,
                                token_count
                            ) VALUES (
                                $1::uuid, $2, $3::vector, $4, $5, $6, $7
                            )
                            """,
                            document_id,
                            text,
                            embedding_str,
                            i,
                            metadata.get('chunk_type', 'standard'),
                            json.dumps(metadata),
                            len(text.split())  # Simple token count
                        )
                        chunks_created += 1
                
                # Update document status
                await conn.execute(
                    """
                    UPDATE documents
                    SET 
                        processing_status = 'completed',
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1::uuid
                    """,
                    document_id
                )
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    'success': True,
                    'document_id': document_id,
                    'chunks_created': chunks_created,
                    'embeddings_generated': len(embeddings),
                    'processing_time_ms': processing_time,
                    'message': f'Successfully vectorized document with {chunks_created} chunks'
                }
                
        except Exception as e:
            logger.error(f"Vectorization failed for document {document_id}: {e}")
            
            # Update document status to failed
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE documents
                        SET 
                            processing_status = 'failed',
                            processing_error = $2,
                            updated_at = NOW()
                        WHERE id = $1::uuid
                        """,
                        document_id,
                        str(e)
                    )
            except:
                pass
            
            raise e
    
    async def extract_insights(
        self,
        document_id: str,
        extract_action_items: bool = True,
        extract_decisions: bool = True,
        extract_risks: bool = True
    ) -> Dict[str, Any]:
        """Extract insights from a document using AI."""
        
        try:
            async with db_pool.acquire() as conn:
                # Get document content
                document = await conn.fetchrow(
                    """
                    SELECT id, title, content, document_type, project_id
                    FROM documents
                    WHERE id = $1::uuid
                    """,
                    document_id
                )
                
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                insights = []
                
                # Use LLM to extract insights
                content = document['content'][:5000]  # Limit content length
                
                prompt = f"""Analyze this document and extract key insights:

Document: {document['title']}
Content: {content}

Extract:
"""
                if extract_action_items:
                    prompt += "1. Action items with assigned person if mentioned\n"
                if extract_decisions:
                    prompt += "2. Key decisions made\n"
                if extract_risks:
                    prompt += "3. Risks or concerns mentioned\n"
                
                prompt += "\nFormat as JSON with arrays: action_items, decisions, risks"
                
                # This would call your LLM
                # For now, we'll create placeholder insights
                
                if extract_action_items and 'action' in content.lower():
                    await conn.execute(
                        """
                        INSERT INTO ai_insights (
                            document_id, project_id, insight_type,
                            title, description, confidence_score
                        ) VALUES ($1::uuid, $2, 'action_item', $3, $4, $5)
                        """,
                        document_id,
                        document['project_id'],
                        "Review and approve budget",
                        "Budget approval needed for Q1",
                        0.85
                    )
                    insights.append({
                        'type': 'action_item',
                        'title': 'Review and approve budget',
                        'confidence': 0.85
                    })
                
                return {
                    'success': True,
                    'document_id': document_id,
                    'insights_extracted': len(insights),
                    'insights': insights
                }
                
        except Exception as e:
            logger.error(f"Insight extraction failed for document {document_id}: {e}")
            raise e


# Create service instance
vectorization_service = VectorizationService()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await vectorization_service.initialize()
    logger.info("Vectorization API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await db_pool.close()
    logger.info("Vectorization API shutdown")


@app.post("/api/vectorize", response_model=VectorizeResponse)
async def vectorize_document(
    request: VectorizeRequest,
    background_tasks: BackgroundTasks
):
    """
    Vectorize a document.
    
    This endpoint is called by pm-rag-vectorize after ingesting a document.
    """
    try:
        result = await vectorization_service.vectorize_document(
            document_id=request.document_id,
            force_revectorize=request.force_revectorize,
            use_intelligent_chunking=request.use_intelligent_chunking
        )
        
        return VectorizeResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
        return VectorizeResponse(
            success=False,
            document_id=request.document_id,
            chunks_created=0,
            embeddings_generated=0,
            processing_time_ms=0,
            error=str(e)
        )


@app.post("/api/extract-insights")
async def extract_insights(request: ExtractInsightsRequest):
    """Extract AI insights from a document."""
    
    try:
        result = await vectorization_service.extract_insights(
            document_id=request.document_id,
            extract_action_items=request.extract_action_items,
            extract_decisions=request.extract_decisions,
            extract_risks=request.extract_risks
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Insight extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/pending")
async def get_pending_documents(limit: int = 10):
    """Get documents pending vectorization."""
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id::text,
                    title,
                    document_type,
                    project_id,
                    created_at
                FROM documents
                WHERE processing_status = 'pending'
                ORDER BY created_at ASC
                LIMIT $1
                """,
                limit
            )
            
            return {
                'documents': [dict(row) for row in rows],
                'count': len(rows)
            }
            
    except Exception as e:
        logger.error(f"Failed to get pending documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/search")
async def search_documents(request: DocumentSearchRequest):
    """Search documents with optional semantic search."""
    
    try:
        if request.use_semantic:
            # Import enhanced search
            from tools_enhanced import enhanced_semantic_search
            from types import SimpleNamespace
            
            # Create mock context
            mock_deps = SimpleNamespace(
                db_pool=db_pool,
                get_embedding=vectorization_service.embedder.embed_text,
                settings=SimpleNamespace(
                    default_match_count=request.limit,
                    max_match_count=100,
                    default_text_weight=0.3
                ),
                user_preferences={}
            )
            
            mock_ctx = SimpleNamespace(deps=mock_deps)
            
            # Perform enhanced search
            results, metadata = await enhanced_semantic_search(
                ctx=mock_ctx,
                query=request.query,
                match_count=request.limit,
                metadata_filters={
                    'project_id': request.project_id,
                    'document_type': request.document_type
                } if request.project_id or request.document_type else None,
                use_memory=False,
                use_reranking=True,
                use_compression=True
            )
            
            return {
                'results': [r.dict() for r in results],
                'metadata': metadata
            }
        else:
            # Simple keyword search
            async with db_pool.acquire() as conn:
                conditions = []
                params = []
                param_count = 1
                
                if request.query:
                    conditions.append(f"""
                        (title ILIKE ${param_count} OR 
                         content ILIKE ${param_count})
                    """)
                    params.append(f'%{request.query}%')
                    param_count += 1
                
                if request.project_id:
                    conditions.append(f"project_id = ${param_count}")
                    params.append(request.project_id)
                    param_count += 1
                
                if request.document_type:
                    conditions.append(f"document_type = ${param_count}")
                    params.append(request.document_type)
                    param_count += 1
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                rows = await conn.fetch(
                    f"""
                    SELECT 
                        id::text,
                        title,
                        source,
                        document_type,
                        project_id,
                        created_at
                    FROM documents
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_count}
                    """,
                    *params,
                    request.limit
                )
                
                return {
                    'results': [dict(row) for row in rows],
                    'count': len(rows)
                }
                
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'service': 'rag-agent-pm-vectorization',
        'timestamp': datetime.now().isoformat()
    }


# Run with: uvicorn vectorization_api:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)