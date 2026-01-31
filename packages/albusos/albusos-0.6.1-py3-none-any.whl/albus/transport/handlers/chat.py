"""Chat endpoint handler.

POST /api/v1/chat - Convenience wrapper for Host agent.

This endpoint provides a simple entry point that delegates to Host agent,
which has full capabilities: memory, conversation history, pathway creation,
agent spawning, and all tools.

For direct agent access, use /api/v1/agents/{id}/turn.
"""

from __future__ import annotations

import logging
import uuid

from aiohttp import web

from albus.infrastructure.errors import ErrorCode
from albus.transport.utils import error_response, get_runtime

logger = logging.getLogger(__name__)


async def handle_chat(request: web.Request) -> web.Response:
    """POST /api/v1/chat - Convenience wrapper for Host agent.
    
    Delegates to Host agent which provides:
    - Conversation history and memory
    - Pathway creation (via pathway.create tool)
    - Agent spawning (via agent.spawn tool)
    - All tools (workspace, code, web, etc.)
    
    This is the recommended entry point for users. Host agent acts as
    a pathway editor, agent editor, and co-creator.
    
    Request body:
        {
            "message": "Create a pathway that summarizes articles",
            "thread_id": "optional-thread-id"  # For conversation continuity
        }
    
    Response:
        {
            "success": true,
            "response": "I've created a pathway...",
            "completed": true,
            "steps_taken": 3,
            "agent_id": "host",
            "thread_id": "..."
        }
    """
    runtime = get_runtime(request)
    
    try:
        body = await request.json()
    except Exception:
        return error_response(request, "Invalid JSON body", ErrorCode.VALIDATION_ERROR, status=400)
    
    message = body.get("message")
    if not message:
        return error_response(request, "Missing 'message' field", ErrorCode.VALIDATION_ERROR, status=400)
    
    # Generate thread_id if not provided (for conversation continuity)
    thread_id = body.get("thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    try:
        # Delegate to Host agent - this provides full capabilities
        result = await runtime.agent_service.turn(
            agent_id="host",
            message=message,
            thread_id=thread_id,
            context=body.get("context"),
            attachments=body.get("attachments"),
        )
        
        return web.json_response(result)
        
    except Exception as e:
        logger.exception("Chat handler error")
        return error_response(request, str(e), ErrorCode.INTERNAL_ERROR, status=500)


__all__ = [
    "handle_chat",
]
