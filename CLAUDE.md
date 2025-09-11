# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a semantic search agent powered by Pydantic AI, PostgreSQL with PGVector, and FastAPI. The system provides intelligent knowledge base search capabilities with both semantic and hybrid search strategies, automatic strategy selection, and result summarization. It includes both CLI and web API interfaces for different deployment scenarios.

## Key Technologies

- **Agent Framework**: Pydantic AI for agent orchestration and tool calling
- **Backend**: FastAPI for REST API with streaming support
- **Database**: PostgreSQL with PGVector extension for vector similarity search
- **LLM Providers**: Multi-provider support (OpenAI, Anthropic, Gemini, Ollama, Groq, etc.)
- **Embeddings**: OpenAI embedding models (text-embedding-3-small/large)
- **Document Processing**: LangChain for text splitting and chunking
- **CLI**: Rich library for interactive command-line interface
- **Search**: Dual semantic and hybrid search strategies with automatic selection

## Common Commands

### Package Installation
```bash
# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Development and Testing
```bash
# Run interactive CLI
python main.py
# OR using package entry point (after installation)
rag-agent

# Run FastAPI server
python server.py
# OR using package entry point
rag-server

# Run document ingestion
python ingest.py --documents examples/documents/
# OR using package entry point
rag-ingest --documents examples/documents/

# Run tests
pytest tests/
pytest tests/test_integration.py  # Integration tests
pytest tests/test_tools.py        # Tool-specific tests

# Code formatting and linting
black .
ruff check .
```

### Database Setup and Management
```bash
# Run database schema setup
psql -d your_database -f sql/schema.sql
# OR run unified schema
psql -d your_database -f sql/unified_schema.sql

# Run database migrations
./sql/run_migrations.sh
```

### Deployment
```bash
# Deploy to Render (using provided script)
./deployment/deploy_to_render.sh

# Start vectorization API
./scripts/start_vectorization_api.sh

# Test deployment
python test_deployment.py
```

## Project Architecture

The system follows a modular agent-based architecture with proper Python package organization:

```
rag-agent-fmglobal/
├── rag_agent/                 # Main Python package
│   ├── core/                  # Core agent components
│   │   ├── agent.py          # Main Pydantic AI agent with tool registration
│   │   ├── dependencies.py   # Agent dependencies and database connection management
│   │   └── prompts.py        # System prompts
│   ├── config/               # Configuration and providers
│   │   ├── settings.py       # Pydantic Settings with environment variable support
│   │   ├── providers.py      # Multi-LLM provider abstractions
│   │   └── llm_providers.py  # Extended provider implementations
│   ├── tools/                # Search tools
│   │   ├── tools.py          # Core search tools (semantic_search, hybrid_search)
│   │   └── tools_enhanced.py # Enhanced search capabilities
│   ├── api/                  # Web API components
│   │   ├── app.py           # FastAPI server with CORS support
│   │   └── vectorization_api.py # Dedicated vectorization API
│   ├── cli/                  # Command-line interface
│   │   └── cli.py           # Rich-based interactive CLI with streaming
│   └── data/                 # Data processing and utilities
│       ├── ingestion/        # Document ingestion pipeline
│       │   ├── ingest.py    # Main ingestion orchestrator
│       │   ├── chunker.py   # Document chunking strategies
│       │   ├── embedder.py  # Embedding generation
│       │   └── intelligent_chunker.py # Advanced chunking
│       └── utils/           # Database and utility functions
│           ├── db_utils.py  # Database connection pooling
│           ├── models.py    # Data models
│           └── conversation_memory.py # Conversation management
├── sql/                      # Database schema and migrations
├── tests/                    # Test suite
├── docs/                     # Documentation
├── deployment/               # Deployment configurations
├── scripts/                  # Utility scripts
├── examples/                 # Example data and frontend
├── main.py                   # CLI entry point
├── server.py                 # API server entry point
├── ingest.py                 # Ingestion entry point
└── setup.py                  # Package configuration
```

## Environment Configuration

Required environment variables (see .env.example):
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/postgres

# LLM Configuration
LLM_PROVIDER=openai                    # openai, anthropic, gemini, ollama, etc.
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini                 # Model name for your provider
LLM_BASE_URL=https://api.openai.com/v1 # API base URL

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small
```

## Search Architecture

The agent intelligently chooses between two search strategies:

### Semantic Search (rag_agent/tools/tools.py:semantic_search)
- Pure vector similarity using embeddings
- Best for conceptual queries and related content discovery
- Uses PostgreSQL match_chunks() function with cosine similarity

### Hybrid Search (rag_agent/tools/tools.py:hybrid_search)  
- Combines semantic search with keyword matching
- Best for specific facts and technical terms
- Uses PostgreSQL hybrid_search() function with weighted scoring
- Configurable text_weight parameter (default 0.3)

The agent automatically selects the appropriate strategy based on query analysis, or users can explicitly request a strategy.

## Database Schema

### Core Tables
- **documents**: Full document storage with metadata
- **chunks**: Document chunks with embeddings (vector column)

### Search Functions
- **match_chunks(query_embedding, match_count)**: Semantic similarity search
- **hybrid_search(query_embedding, query_text, match_count, text_weight)**: Combined search

## CLI Features

The interactive CLI (rag_agent/cli/cli.py) provides:
- Real-time streaming responses with tool execution visibility
- Session persistence and conversation history
- User preference management with `set` commands
- Rich formatting and syntax highlighting
- Commands: `help`, `info`, `clear`, `set key=value`, `exit/quit`

## Deployment Patterns

### Local Development
- Use CLI for interactive testing: `python main.py`
- FastAPI for web interface: `python server.py`

### Production Deployment  
- **Backend**: Render deployment via deployment/render.yaml configuration
- **Frontend Integration**: FastAPI with CORS for Next.js frontends
- **Streaming**: Server-Sent Events for real-time responses

## Testing Strategy

- **Unit Tests**: Individual component testing (tests/test_tools.py, tests/test_agent.py)
- **Integration Tests**: End-to-end workflow testing (tests/test_integration.py)  
- **Deployment Tests**: Production readiness validation (test_deployment.py)
- **Enhanced RAG Tests**: Advanced search capabilities (test_enhanced_rag.py)

## Key Development Patterns

### CRITICAL: Pydantic AI AgentRunResult Handling
**⚠️ IMPORTANT: When using `agent.run()`, the result object structure varies between Pydantic AI versions.**

Always use this safe extraction pattern to avoid AttributeError:
```python
result = await agent.run(prompt, deps=deps)

# CORRECT: Safe extraction with fallbacks
if hasattr(result, 'data'):
    response_text = result.data  # Most common - direct access
elif hasattr(result, 'response'):
    response_text = str(result.response)
elif hasattr(result, 'output'):
    response_text = str(result.output)
else:
    # Extract from string representation as last resort
    result_str = str(result)
    # Use regex to extract if needed
```

**NEVER do this:**
```python
# ❌ WRONG - Will cause AttributeError
response_text = result.data  # May not exist!

# ❌ WRONG - Includes wrapper text
response_text = str(result)  # Returns "AgentRunResult(output='...')"
```

See `/documentation/technical/pydantic-ai-agentrunresult-fix.md` for complete details.

### Agent Tool Registration
```python
from pydantic_ai import Agent
from rag_agent.tools.tools import semantic_search, hybrid_search
from rag_agent.core.dependencies import AgentDependencies

agent = Agent(model, deps_type=AgentDependencies)
agent.tool(semantic_search)  # Register search tools
agent.tool(hybrid_search)
```

### Database Context Management
- Connection pooling via AgentDependencies
- Async context managers for database operations
- Proper connection lifecycle in tools

### Multi-Provider LLM Support
- Provider abstraction in rag_agent/config/providers.py
- OpenAI-compatible API interface
- Model configuration via environment variables

## Document Ingestion Workflow

1. **Document Processing**: Parse markdown/text documents in documents/
2. **Chunking**: Split documents using LangChain text splitters  
3. **Embedding Generation**: Create embeddings via OpenAI API
4. **Database Storage**: Insert documents and chunks with vectors
5. **Validation**: Verify ingestion success and search readiness

Required before first use: `python ingest.py --documents examples/documents/`