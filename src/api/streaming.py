# Streaming utilities for long LLM responses
from typing import AsyncGenerator, Any, Dict
from fastapi import Request
from fastapi.responses import StreamingResponse
import json
import asyncio


async def create_sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    """Create a Server-Sent Events response from an async generator.
    
    SSE format: data: <message>\n\n
    """
    async def event_generator():
        try:
            async for chunk in generator:
                # Format as SSE event
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def stream_llm_response(
    llm,
    messages: list,
    chunk_callback: callable = None
) -> AsyncGenerator[str, None]:
    """Stream responses from an LLM call.
    
    Args:
        llm: The LangChain LLM instance
        messages: Messages to send to the LLM
        chunk_callback: Optional callback for each chunk
        
    Yields:
        String chunks of the response
    """
    try:
        # Use LangChain's streaming
        async for chunk in llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                if chunk_callback:
                    chunk_callback(chunk.content)
                yield chunk.content
    except Exception as e:
        yield f"\n[Error: {str(e)}]"


def create_stream_event(event_type: str, data: Any) -> str:
    """Create a properly formatted SSE event.
    
    Args:
        event_type: Type of event (e.g., 'message', 'done', 'error')
        data: Data to include in the event
        
    Returns:
        Formatted SSE string
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
