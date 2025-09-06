# Enhanced RAG System Setup Guide

## 🚀 Quick Start

Follow these steps to set up and test your enhanced RAG system with all advanced features.

## Prerequisites

1. **PostgreSQL with pgvector extension**
   - PostgreSQL 14+ recommended
   - pgvector extension for vector similarity search

2. **Python 3.9+**
   - Required for async support and type hints

3. **API Keys (at least one required)**
   - OpenAI API key (recommended)
   - Anthropic API key (optional)
   - Cohere API key (for reranking)
   - Groq API key (optional)

## Step 1: Environment Setup

### 1.1 Create `.env` file

Create a `.env` file in the `rag-agent-pm` directory:

```bash
# Database (Supabase or your PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/your_db

# LLM Providers (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key  # Optional
COHERE_API_KEY=your-cohere-key  # For reranking
GROQ_API_KEY=your-groq-key  # Optional

# Optional: Specific Supabase credentials if using Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
```

### 1.2 Install Dependencies

```bash
cd monorepo-agents/rag-agent-pm
pip install -r requirements.txt

# Download NLTK data (for intelligent chunking)
python -c "import nltk; nltk.download('punkt')"
```

## Step 2: Database Setup

### 2.1 Run Database Migrations

```bash
# Make sure you're in the rag-agent-pm directory
cd monorepo-agents/rag-agent-pm

# Run the migration script
./sql/run_migrations.sh
```

If the script doesn't work, run manually:

```bash
# Set your database URL
export DATABASE_URL="postgresql://user:password@host:port/database"

# Run SQL files
psql $DATABASE_URL -f sql/schema.sql
psql $DATABASE_URL -f sql/conversation_memory.sql
```

### 2.2 Verify Database Setup

```sql
-- Connect to your database and run:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'conversations', 
    'conversation_messages', 
    'documents', 
    'chunks'
);
-- Should return 4+ rows
```

## Step 3: Test the Enhanced Features

### 3.1 Run the Test Suite

```bash
# Run the comprehensive test
python test_enhanced_rag.py
```

Expected output:
```
✅ conversation_memory: PASSED
✅ query_enhancement: PASSED
✅ metadata_filtering: PASSED
✅ reranking: PASSED
✅ context_compression: PASSED
✅ intelligent_chunking: PASSED
✅ full_pipeline: PASSED

🎉 All tests passed! Your enhanced RAG system is ready.
```

### 3.2 Test Individual Components

```python
# Test conversation memory
from utils.conversation_memory import ConversationMemoryManager
memory = ConversationMemoryManager(db_pool, embedding_fn)
conversation_id = await memory.create_or_get_conversation("session-001")

# Test query enhancement
from llm_providers import enhance_query
enhanced = await enhance_query("What's the budget?", context="Project Alpha discussion")

# Test reranking
from llm_providers import rerank_documents
reranked = await rerank_documents(query, documents, top_k=10)
```

## Step 4: Integration with Your App

### 4.1 Update Your RAG Agent

```python
# In your agent.py or main app file
from tools_enhanced import enhanced_semantic_search
from utils.conversation_memory import ConversationMemoryManager

# Use enhanced search
results, metadata = await enhanced_semantic_search(
    ctx,
    query="What was discussed about the budget?",
    conversation_id=session_id,
    metadata_filters={"project_id": project_id},
    use_memory=True,
    use_reranking=True,
    use_compression=True
)
```

### 4.2 Process Documents with Intelligent Chunking

```python
from ingestion.intelligent_chunker import IntelligentChunker

chunker = IntelligentChunker(
    base_chunk_size=1000,
    enable_hierarchical=True,
    enable_semantic=True
)

chunks, metadata = await chunker.chunk_document(
    content=document_text,
    document_id=doc_id,
    metadata={"project_id": 1, "document_type": "meeting"}
)
```

## Step 5: Production Deployment

### 5.1 Environment Variables for Production

```bash
# Production settings
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
MAX_CONVERSATION_MESSAGES=50
COMPRESSION_THRESHOLD=50
SUMMARIZATION_THRESHOLD=100
```

### 5.2 Monitoring & Maintenance

```sql
-- Monitor conversation memory usage
SELECT 
    COUNT(DISTINCT conversation_id) as total_conversations,
    COUNT(*) as total_messages,
    SUM(CASE WHEN is_compressed THEN 1 ELSE 0 END) as compressed_messages
FROM conversation_messages;

-- Check chunk distribution
SELECT 
    metadata->>'document_type' as doc_type,
    COUNT(*) as chunk_count
FROM chunks
GROUP BY metadata->>'document_type';
```

## Troubleshooting

### Common Issues

1. **"pgvector extension not found"**
   ```sql
   CREATE EXTENSION vector;
   ```

2. **"No LLM provider available"**
   - Ensure at least one API key is set in `.env`
   - Check API key validity

3. **"Database connection failed"**
   - Verify DATABASE_URL format
   - Check PostgreSQL is running
   - Ensure database exists

4. **"Embedding dimension mismatch"**
   - Ensure using consistent embedding model
   - Default is OpenAI's 1536-dimension embeddings

### Performance Tuning

1. **Optimize chunk retrieval**
   ```sql
   -- Add indexes for better performance
   CREATE INDEX idx_chunks_project ON chunks((metadata->>'project_id'));
   CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id, message_index);
   ```

2. **Adjust memory settings**
   ```python
   memory_manager = ConversationMemoryManager(
       db_pool=pool,
       embedding_function=embed_fn,
       max_working_memory=30,  # Increase for longer context
       compression_threshold=100,  # Compress after more messages
   )
   ```

## Feature Configuration

### Conversation Memory
- `max_working_memory`: Number of recent messages to keep in memory (default: 20)
- `importance_threshold`: Score for long-term retention (default: 0.7)
- `compression_threshold`: Messages before compression (default: 50)

### Query Enhancement
- HyDE temperature: 0.7 (creative hypothetical answers)
- Entity extraction: Automatic from capitalized words
- Sub-query generation: Automatic for complex queries

### Reranking
- Cross-encoder model: `rerank-english-v2.0` (Cohere)
- MMR lambda: 0.5 (balance relevance/diversity)
- Recency boost: Exponential decay with 30-day half-life

### Context Compression
- Max chunk length: 1500 characters
- Compression method: Relevant sentence extraction
- LLM summarization: Optional for long chunks

### Intelligent Chunking
- Base chunk size: 1000 characters
- Overlap: 200 characters
- Hierarchical levels: 2 (parent/child)
- Sentence window: 3 sentences

## Next Steps

1. **Ingest your documents** with intelligent chunking
2. **Configure LLM providers** for your use case
3. **Set up monitoring** for conversation memory
4. **Fine-tune parameters** based on your data
5. **Add custom metadata** for better filtering

## Support

For issues or questions:
1. Check test output: `python test_enhanced_rag.py`
2. Review logs in your application
3. Check database connectivity and migrations
4. Verify API keys are valid

---

Your Enhanced RAG system is now ready with:
✅ Persistent conversation memory
✅ Smart query enhancement
✅ Advanced reranking
✅ Context compression
✅ Metadata filtering
✅ Intelligent chunking

Start building amazing RAG applications! 🚀