import { NextRequest, NextResponse } from 'next/server';

// Configure your FM Global API endpoint
const FM_GLOBAL_API_URL = process.env.NEXT_PUBLIC_FM_GLOBAL_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward the request to FM Global API
    const response = await fetch(`${FM_GLOBAL_API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: body.query,
        asrs_topic: body.asrs_topic,
        design_focus: body.design_focus,
        conversation_history: body.conversation_history || []
      }),
    });

    if (!response.ok) {
      throw new Error(`FM Global API error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('FM Global API error:', error);
    return NextResponse.json(
      { error: 'Failed to get FM Global response' },
      { status: 500 }
    );
  }
}

// Streaming endpoint
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get('query');
  
  if (!query) {
    return NextResponse.json(
      { error: 'Query parameter is required' },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(`${FM_GLOBAL_API_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        asrs_topic: searchParams.get('asrs_topic'),
        design_focus: searchParams.get('design_focus'),
      }),
    });

    if (!response.ok) {
      throw new Error(`FM Global API error: ${response.statusText}`);
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
    
  } catch (error) {
    console.error('FM Global streaming error:', error);
    return NextResponse.json(
      { error: 'Failed to stream FM Global response' },
      { status: 500 }
    );
  }
}