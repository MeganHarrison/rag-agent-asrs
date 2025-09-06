# Next.js Integration Guide for FM Global RAG Agent

## Overview
This guide explains how to integrate the FM Global 8-34 ASRS Expert API with your Next.js frontend at https://alleato-ai-dashboard.vercel.app/ or any local Next.js application.

## API Endpoints

The FM Global API provides two main endpoints:

### 1. Synchronous Chat Endpoint
- **URL**: `POST /chat`
- **Response**: JSON with complete response

### 2. Streaming Chat Endpoint  
- **URL**: `POST /chat/stream`
- **Response**: Server-Sent Events (SSE) for real-time streaming

## Setup Instructions

### Step 1: Start the FM Global API Server

Choose one of these options:

#### Option A: Production Server (with Supabase)
```bash
cd rag-agent-fmglobal
source venv/bin/activate
python -m rag_agent.api.fm_global_app
# Server runs on http://localhost:8000
```

#### Option B: Demo Server (no database required)
```bash
cd rag-agent-fmglobal
source venv/bin/activate
python fm_global_demo_server.py
# Server runs on http://localhost:8003
```

### Step 2: Add to Your Next.js Project

1. **Copy the integration files** to your Next.js project:
   ```bash
   # Copy API route
   cp frontend/nextjs-integration/app/api/fm-global/route.ts \
      your-nextjs-app/app/api/fm-global/route.ts
   
   # Copy chat component
   cp frontend/nextjs-integration/components/fm-global-chat.tsx \
      your-nextjs-app/components/fm-global-chat.tsx
   
   # Copy page (optional)
   cp frontend/nextjs-integration/app/fm-global/page.tsx \
      your-nextjs-app/app/fm-global/page.tsx
   ```

2. **Set environment variables** in your Next.js `.env.local`:
   ```env
   # For local development
   NEXT_PUBLIC_FM_GLOBAL_API_URL=http://localhost:8000
   
   # For production (when API is deployed)
   NEXT_PUBLIC_FM_GLOBAL_API_URL=https://your-api.onrender.com
   ```

3. **Import and use the component** in any page:
   ```tsx
   import { FMGlobalChat } from '@/components/fm-global-chat';
   
   export default function YourPage() {
     return (
       <div>
         <h1>FM Global Expert</h1>
         <FMGlobalChat />
       </div>
     );
   }
   ```

## Direct API Integration (Without Component)

If you prefer to integrate directly with your existing chat interface:

```typescript
// Example API call from your Next.js frontend
async function askFMGlobal(query: string) {
  const response = await fetch('/api/fm-global', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      asrs_topic: 'fire_protection', // optional
      design_focus: 'cost_optimization', // optional
      conversation_history: [] // optional
    }),
  });

  const data = await response.json();
  return data;
}

// Using the response
const result = await askFMGlobal("What are the aisle width requirements?");
console.log(result.response); // The answer
console.log(result.tables_referenced); // Referenced tables
console.log(result.figures_referenced); // Referenced figures
```

## Streaming Response Integration

For real-time streaming responses:

```typescript
async function streamFMGlobal(query: string, onChunk: (chunk: string) => void) {
  const response = await fetch('/api/fm-global?query=' + encodeURIComponent(query), {
    method: 'GET',
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'content') {
          onChunk(data.content);
        }
      }
    }
  }
}
```

## CORS Configuration

The API is pre-configured to accept requests from:
- `https://alleato-ai-dashboard.vercel.app`
- `http://localhost:3000-3006`
- Any `*.vercel.app` domain

## Deployment

### Deploy the API to Render

1. **Create a new Web Service on Render**
2. **Connect your GitHub repository**
3. **Configure the service**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn rag_agent.api.fm_global_app:app --host 0.0.0.0 --port $PORT`
   
4. **Add environment variables**:
   ```
   DATABASE_URL=your_supabase_url
   LLM_API_KEY=your_openai_key
   LLM_MODEL=gpt-3.5-turbo
   ```

5. **Update your Next.js environment**:
   ```env
   NEXT_PUBLIC_FM_GLOBAL_API_URL=https://your-service.onrender.com
   ```

### Deploy Frontend to Vercel

Your Next.js app at https://alleato-ai-dashboard.vercel.app/ just needs the environment variable:

1. Go to Vercel Dashboard → Settings → Environment Variables
2. Add: `NEXT_PUBLIC_FM_GLOBAL_API_URL` = `https://your-api.onrender.com`
3. Redeploy

## API Response Format

### Successful Response
```json
{
  "response": "According to FM Global 8-34...",
  "session_id": "uuid",
  "tables_referenced": ["Table 2-1", "Table 4-3"],
  "figures_referenced": ["Figure 3-2"],
  "asrs_topics": ["fire_protection", "rack_design"]
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Features

- ✅ Real-time streaming responses
- ✅ Topic filtering (fire protection, seismic, etc.)
- ✅ Conversation history support
- ✅ Table/figure reference extraction
- ✅ Cost optimization suggestions
- ✅ ASRS design guidance

## Testing

1. **Test locally first**:
   ```bash
   # Terminal 1: Start API
   python fm_global_demo_server.py
   
   # Terminal 2: Test with curl
   curl -X POST http://localhost:8003/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "What are aisle width requirements?"}'
   ```

2. **Test from your Next.js app**:
   - Navigate to `/fm-global` page
   - Try example questions
   - Verify responses are working

## Troubleshooting

### CORS Issues
- Ensure your domain is in the `allow_origins` list in `fm_global_app.py`
- Check browser console for specific CORS errors

### Connection Errors
- Verify the API server is running
- Check the `NEXT_PUBLIC_FM_GLOBAL_API_URL` is correct
- Ensure firewall/network allows the connection

### Database Errors
- Use the demo server if Supabase is not configured
- Check DATABASE_URL environment variable
- Verify Supabase tables exist (fm_documents, fm_text_chunks, etc.)

## Support

For issues or questions:
- GitHub: https://github.com/MeganHarrison/rag-agent-asrs
- API Documentation: `/docs` endpoint when server is running