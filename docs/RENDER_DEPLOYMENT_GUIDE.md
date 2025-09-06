# Render Deployment Guide for RAG Agent PM

This guide provides step-by-step instructions to deploy the Python RAG agent to Render using the prepared configuration files.

## Prerequisites

- Render account (free tier available)
- GitHub repository with the RAG agent code
- Required API keys (OpenAI, Anthropic, Cohere)

## Repository Information

- **GitHub Repository**: `https://github.com/MeganHarrison/rag-agent-pm`
- **Branch**: `main`
- **Project Path**: Root directory contains all necessary files

## Deployment Steps

### 1. Create PostgreSQL Database

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure database:
   - **Name**: `rag-database`
   - **Database**: `rag_production`
   - **User**: `rag_user`
   - **Plan**: `Starter` (free tier) or `Standard` for production
4. Click **"Create Database"**
5. **Important**: Copy the database connection string for later use

### 2. Deploy RAG Agent API Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `MeganHarrison/rag-agent-pm`
3. Configure the service:
   - **Name**: `rag-agent-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -c 'import nltk; nltk.download("punkt")'
     ```
   - **Start Command**:
     ```bash
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```

4. **Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4
   LLM_API_KEY=[Your OpenAI API Key]
   LLM_BASE_URL=https://api.openai.com/v1
   OPENAI_API_KEY=[Your OpenAI API Key]
   ANTHROPIC_API_KEY=[Your Anthropic API Key]
   COHERE_API_KEY=[Your Cohere API Key for reranking]
   GROQ_API_KEY=[Your Groq API Key - Optional]
   DATABASE_URL=[PostgreSQL connection string from step 1]
   ```

5. Click **"Create Web Service"**

### 3. Deploy Vectorization API Service

1. Click **"New +"** → **"Web Service"**
2. Connect the same repository: `MeganHarrison/rag-agent-pm`
3. Configure the service:
   - **Name**: `rag-vectorization-api`
   - **Region**: Same as main service
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -c 'import nltk; nltk.download("punkt")' && if [ -f "sql/unified_schema.sql" ]; then psql $DATABASE_URL -f sql/unified_schema.sql || true; fi
     ```
   - **Start Command**:
     ```bash
     uvicorn vectorization_api:app --host 0.0.0.0 --port $PORT
     ```

4. **Environment Variables**:
   ```
   OPENAI_API_KEY=[Your OpenAI API Key]
   DATABASE_URL=[Same PostgreSQL connection string]
   ANTHROPIC_API_KEY=[Your Anthropic API Key - Optional]
   COHERE_API_KEY=[Your Cohere API Key]
   ```

5. Click **"Create Web Service"**

### 4. Apply Database Schema (Manual Step)

If the automatic schema application fails during build, you can apply it manually:

1. Connect to your PostgreSQL database using the connection string
2. Run the SQL files in order:
   ```sql
   -- First, run the unified schema
   \i sql/unified_schema.sql
   
   -- Then, run conversation memory schema
   \i sql/conversation_memory.sql
   ```

### 5. Verify Deployment

Once both services are deployed, you should see:

1. **RAG Agent API**: `https://rag-agent-api.onrender.com`
2. **Vectorization API**: `https://rag-vectorization-api.onrender.com`

#### Health Check Endpoints

- **Main API Health**: `GET https://rag-agent-api.onrender.com/health`
- **Vectorization API Health**: `GET https://rag-vectorization-api.onrender.com/health`

#### Test Endpoints

- **Chat**: `POST https://rag-agent-api.onrender.com/chat`
- **Vectorization**: `POST https://rag-vectorization-api.onrender.com/vectorize`

## Configuration Details

### Required Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM and embeddings | Both services |
| `DATABASE_URL` | PostgreSQL connection string | Both services |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Optional |
| `COHERE_API_KEY` | Cohere API key for reranking | Optional |
| `GROQ_API_KEY` | Groq API key for fast inference | Optional |
| `LLM_PROVIDER` | Primary LLM provider (default: openai) | Main API only |
| `LLM_MODEL` | Model name (default: gpt-4) | Main API only |
| `LLM_BASE_URL` | API base URL | Main API only |

### Service Specifications

#### RAG Agent API
- **Purpose**: Main chat interface and RAG queries
- **Port**: Dynamic (`$PORT` environment variable)
- **Scaling**: Auto-scaling based on traffic
- **Health Check**: `/health` endpoint

#### Vectorization API  
- **Purpose**: Document processing and embedding generation
- **Port**: Dynamic (`$PORT` environment variable)
- **Scaling**: Auto-scaling for batch processing
- **Health Check**: `/health` endpoint

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all dependencies in `requirements.txt` are valid
   - Verify Python version compatibility
   - Check build logs for specific error messages

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is correctly set
   - Ensure database is running and accessible
   - Check network connectivity between services

3. **API Key Issues**
   - Verify all required API keys are set
   - Check key permissions and rate limits
   - Test keys independently if needed

4. **Import Errors**
   - Ensure all custom modules are in the correct directory structure
   - Check for circular imports
   - Verify all dependencies are installed

### Monitoring

- Check service logs in Render Dashboard
- Monitor resource usage and scaling events
- Set up alerts for service downtime

## Next Steps

After successful deployment:

1. Test the APIs with sample requests
2. Monitor performance and adjust scaling settings
3. Set up custom domain names if needed
4. Configure CI/CD for automatic deployments
5. Implement monitoring and logging

## Support

- Check Render documentation: https://render.com/docs
- Review service logs for error details
- Contact support if deployment issues persist

---

**Note**: This deployment uses the Infrastructure as Code approach with the `render.yaml` configuration file, ensuring consistent and reproducible deployments.