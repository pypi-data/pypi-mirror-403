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
    expert_id: str = "default",
    domain: str = "general",
) -> Dict[str, Any]:
    """Create memories from conversation history

    Args:
        messages: Conversation message list, format [{"role": "user|assistant", "content": "..."}]
        session_id: Session ID
        expert_id: Expert ID (default "default")
        domain: Business domain (default "general")

    Returns:
        Creation result, contains status and memories/data fields

    Example:
        result = await create_memory(
            messages=[
                {"role": "user", "content": "Hello, my name is Zhang San"},
                {"role": "assistant", "content": "Hello Zhang San, nice to meet you"}
            ],
            session_id="sess_456",
            expert_id="agent_001",
            domain="customer_service"
        )
    """
    # Read API Key and User ID from environment variables
    api_key = get_api_key()
    user_id = get_user_id()

    request_body = {
        "expert_id": expert_id,
        "session_id": session_id,
        "messages": [
            {"role": msg.get("role"), "content": msg.get("content")} for msg in messages
        ],
        "format": "simple",
    }

    if domain:
        request_body["domain"] = domain
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
    query: Optional[str] = None,
    layer: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Search/query memories

    Args:
        query: Search keyword
        layer: Memory layer L1-L5
        domain: Business domain
        limit: Return count (default 10)

    Returns:
        Search result list

    Example:
        result = await search_memories(
            query="Zhang San",
            layer="L1",
            limit=5
        )
    """
    # Read API Key and User ID from environment variables
    api_key = get_api_key()
    user_id = get_user_id()

    params = {"size": limit}

    if query:
        params["keywords"] = [query]
    if layer:
        params["layer"] = layer
    if domain:
        params["domain"] = domain
    if user_id:
        params["user_id"] = user_id

    return await call_api("GET", Config.MEMORY_QUERY_PATH, api_key, params=params)


# @mcp.tool()
# def ready() -> str:
#     """Confirm service is ready"""
#     return "ready"
