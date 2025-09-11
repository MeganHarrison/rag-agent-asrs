# FM Global RAG Agent Troubleshooting Guide

## Common Issues and Solutions

### 1. AgentRunResult AttributeError

**Error Message:**
```
'AgentRunResult' object has no attribute 'data'
```

**Solution:**
The fix is already implemented in `rag_agent/api/fm_global_app.py`. The code uses a safe fallback chain:
```python
if hasattr(result, 'data'):
    response_text = result.data
elif hasattr(result, 'response'):
    response_text = str(result.response)
elif hasattr(result, 'output'):
    response_text = str(result.output)
else:
    # Extract from string representation
```

**If it happens again:**
1. Check Pydantic AI version in requirements.txt
2. Verify the extraction pattern is still in place
3. Test locally with `python test_agent_pipeline.py`

### 2. Response Contains AgentRunResult Wrapper

**Problem:**
Response shows: `AgentRunResult(output='actual text here')`

**Solution:**
Already fixed by prioritizing direct `.data` access over string conversion.

**Prevention:**
- Never use `str(result)` as the first option
- Always check for `.data` attribute first
- Test responses before deployment

### 3. Database/Vector Search Errors

**Common Errors:**
- `invalid input for query argument $1: [array] (expected str, got list)`
- `structure of query does not match function result type`

**These are separate issues** from the AgentRunResult fix and relate to:
- Database schema mismatches
- Embedding dimension conflicts
- SQL function parameter types

**Solutions:**
1. Check database schema matches expected format
2. Verify embedding dimensions (1536 for OpenAI)
3. Review SQL functions in `/sql/` directory

### 4. Railway Deployment Issues

**Health Check Works but Chat Fails:**

1. **Check API Keys:**
   ```bash
   # In Railway dashboard, verify:
   LLM_API_KEY=your-openai-key
   DATABASE_URL=your-postgres-url
   ```

2. **Cold Start Issues:**
   - First request may timeout
   - Retry after 30-60 seconds
   - Consider upgrading from free tier

3. **CORS Errors:**
   - Verify allowed origins in `fm_global_app.py`
   - Add your domain to CORS middleware

### 5. Testing After Fixes

**Local Testing:**
```python
# Quick test script
python -c "
import asyncio
from rag_agent.api.fm_global_app import FMGlobalQuery, chat_sync

async def test():
    query = FMGlobalQuery(query='Test')
    response = await chat_sync(query)
    print('Clean?' , 'AgentRunResult' not in response.response)
    
asyncio.run(test())
"
```

**Production Testing:**
```bash
# Health check
curl https://fm-global-asrs-expert-production-afb0.up.railway.app/health

# Chat test
curl -X POST https://fm-global-asrs-expert-production-afb0.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | jq .
```

## File Locations

Key files to check when troubleshooting:

1. **Main API:** `/rag_agent/api/fm_global_app.py`
   - Chat endpoints
   - Response extraction logic

2. **Agent Definition:** `/rag_agent/core/fm_global_agent.py`
   - Agent configuration
   - Tool registration

3. **Server Entry:** `/start_server.py`
   - Server configuration
   - Error handling

4. **Dependencies:** `/rag_agent/core/dependencies.py`
   - Database connections
   - Settings management

## Debugging Commands

```bash
# Check recent commits for fixes
git log --oneline -10 | grep -i fix

# Find all agent.run calls
grep -r "agent.run" --include="*.py"

# Check for response extraction patterns
grep -r "result.data\|result.response" --include="*.py"

# Test the fix locally
python test_agent_pipeline.py
```

## Prevention Checklist

Before deploying:
- [ ] Test chat endpoint locally
- [ ] Verify no AgentRunResult in responses
- [ ] Check health endpoint
- [ ] Confirm environment variables set
- [ ] Test with actual queries, not just health checks

## Support

If issues persist after following this guide:
1. Check commits `1c6c06f` and `177d76e` for the working fix
2. Review `/documentation/technical/pydantic-ai-agentrunresult-fix.md`
3. Test with the patterns shown above
4. Ensure Railway has redeployed after pushing fixes

## Last Updated
- Date: 2025-09-09
- Fixed Version: Deployed to Railway
- Commits: 1c6c06f, 177d76e