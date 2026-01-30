"""TiMEM MCP Service Module

Provides two core tools: create_memory and search_memories
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .client import call_api
from .config import get_api_key, get_user_id, Config

__version__ = "0.1.0"

# Create MCP server instance
mcp = FastMCP("TiMEM")


@mcp.tool()
async def create_memory(
    messages: List[Dict[str, str]],
    session_id: str,
) -> Dict[str, Any]:
    """Create memories from conversation history

    Args:
        messages: Conversation message list, format [{"role": "user|assistant", "content": "..."}]
        session_id: Session ID

    Returns:
        Creation result, contains status and memories/data fields

    Example:
        result = await create_memory(
            messages=[
                {"role": "user", "content": "Hello, my name is Zhang San"},
                {"role": "assistant", "content": "Hello Zhang San, nice to meet you"}
            ],
            session_id="sess_456",
        )
    """
    # Read API Key and User ID from environment variables
    api_key = get_api_key()
    user_id = get_user_id()

    request_body = {
        "expert_id": "default-expert-001",
        "session_id": session_id,
        "messages": [
            {"role": msg.get("role"), "content": msg.get("content")} for msg in messages
        ],
        "format": "compact",
    }

    # if domain:
    #     request_body["domain"] = domain
    if user_id:
        request_body["user_id"] = user_id

    response = await call_api(
        "POST", Config.MEMORY_CREATE_PATH, api_key, json_data=request_body, timeout=60.0
    )

    # Main service returns list format, need to wrap as dict
    if isinstance(response, list):
        return {"status": "success", "memories": response, "count": len(response)}
    return response


@mcp.tool()
async def search_memories(
    query_text: Optional[str] = None,
    layer: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Search memories

    Args:
        query_text: Search keyword
        layer: Memory layer L1-L5
        limit: Return count (default 10)

    Returns:
        Search result list

    Example:
        result = await search_memories(
            query_text="Zhang San",
            layer="L1",
            limit=5
        )
    """
    # Read API Key and User ID from environment variables
    api_key = get_api_key()
    user_id = get_user_id()

    params = {"size": limit}

    if query_text:
        params["keywords"] = [query_text]
    if layer:
        params["layer"] = layer
    # if domain:
    #     params["domain"] = domain
    if user_id:
        params["user_id"] = user_id

    params["format"] = "simple"

    return await call_api("GET", Config.MEMORY_QUERY_PATH, api_key, params=params)


# @mcp.tool()
# def ready() -> str:
#     """Confirm service is ready"""
#     return "ready"
