// Example Next.js API route for your Vercel frontend
// Place this in your Next.js app at: app/api/chat/route.ts

export async function POST(req: Request) {
  const { message, conversation_history, session_id } = await req.json()
  
  // Your Render backend URL (update after deployment)
  const BACKEND_URL = process.env.BACKEND_URL || 'https://your-rag-agent.onrender.com'
  
  try {
    // For streaming responses
    const response = await fetch(`${BACKEND_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_history,
        session_id
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`)
    }
    
    // Return the stream directly to the client
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Chat API error:', error)
    return Response.json(
      { error: 'Failed to process chat request' },
      { status: 500 }
    )
  }
}