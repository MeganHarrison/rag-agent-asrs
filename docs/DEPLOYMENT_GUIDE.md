# RAG Agent Deployment Guide

## Architecture Overview
- **Backend**: Python FastAPI server (Deploy on Render)
- **Frontend**: Next.js application (Deploy on Vercel)
- **Communication**: REST API with streaming support via Server-Sent Events

## Backend Deployment (Render)

### 1. Prepare Your Repository
```bash
# Ensure these files are in your rag_agent_pm folder:
- app.py (FastAPI server)
- render.yaml (Render configuration)
- requirements.txt (Python dependencies)
- All your agent files (agent.py, tools.py, etc.)
```

### 2. Deploy to Render

#### Option A: Using Render Dashboard
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the branch with your RAG agent
5. Set the root directory to `use-cases/agent-factory-with-subagents/agents/rag_agent_pm`
6. Render will auto-detect the `render.yaml` file
7. Add environment variables in the dashboard:
   - `LLM_API_KEY`: Your OpenAI/Anthropic API key
   - `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)
   - `ANTHROPIC_API_KEY`: Anthropic API key (if using Claude)
8. Click "Create Web Service"

#### Option B: Using Render CLI
```bash
# Install Render CLI
brew tap render-oss/render
brew install render

# Deploy
cd use-cases/agent-factory-with-subagents/agents/rag_agent_pm
render create
```

### 3. Configure Environment Variables
In Render dashboard, add:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=<your-api-key>
LLM_BASE_URL=https://api.openai.com/v1
```

### 4. Note Your Backend URL
After deployment, you'll get a URL like:
`https://rag-agent-api-xxxx.onrender.com`

## Frontend Deployment (Vercel)

### 1. Prepare Your Next.js App
```bash
# In your Next.js project, add:
- app/api/chat/route.ts (API route)
- components/chat.tsx (Chat UI component)
```

### 2. Update Environment Variables
Create `.env.local` in your Next.js project:
```
BACKEND_URL=https://rag-agent-api-xxxx.onrender.com
```

### 3. Deploy to Vercel

#### Option A: Using Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts and add environment variable:
# BACKEND_URL = your Render backend URL
```

#### Option B: Using Vercel Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Add environment variable:
   - Name: `BACKEND_URL`
   - Value: Your Render backend URL
4. Deploy

### 4. Update CORS Settings
After getting your Vercel URL, update `app.py` CORS origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app"  # Add your actual Vercel URL
    ],
    # ... rest of config
)
```

## Testing the Deployment

### Test Backend (Render)
```bash
# Health check
curl https://your-backend.onrender.com/health

# Test chat endpoint
curl -X POST https://your-backend.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test message"}'
```

### Test Frontend (Vercel)
1. Navigate to your Vercel URL
2. Open the chat interface
3. Send a test message
4. Verify streaming responses work

## Monitoring & Logs

### Render Backend
- View logs: Render Dashboard → Your Service → Logs
- Monitor metrics: Dashboard → Metrics tab
- Set up alerts for errors or downtime

### Vercel Frontend
- View function logs: Vercel Dashboard → Functions tab
- Monitor analytics: Dashboard → Analytics
- Set up error tracking with Sentry (optional)

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure your Vercel domain is in the CORS allowed origins
   - Check that credentials are included in fetch requests

2. **Connection Timeouts**
   - Render free tier may sleep after inactivity
   - Consider upgrading to keep service always-on

3. **Streaming Not Working**
   - Ensure `X-Accel-Buffering: no` header is set
   - Check that SSE parsing is correct in frontend

4. **Environment Variables Not Loading**
   - Verify `.env` file exists in backend
   - Check that variables are set in Render dashboard
   - Ensure `python-dotenv` is installed

## Cost Considerations

### Render (Backend)
- **Free Tier**: 750 hours/month, sleeps after 15 min inactivity
- **Paid**: $7/month for always-on instance
- **Recommended**: Start with free, upgrade if needed

### Vercel (Frontend)
- **Free Tier**: Generous limits for personal projects
- **Pro**: $20/month for team features
- **Recommended**: Free tier is usually sufficient

## Next Steps

1. Set up GitHub Actions for CI/CD
2. Add authentication (Supabase, Auth0, etc.)
3. Implement rate limiting
4. Add monitoring (Sentry, LogRocket)
5. Set up database persistence for chat history
6. Add vector database hosting if needed (Pinecone, Weaviate)