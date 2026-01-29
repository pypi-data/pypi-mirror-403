"""TiMEM MCP 服务模块

提供 create_memory 和 search_memories 两个核心工具
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .client import call_api
from .config import get_api_key, get_user_id, Config

__version__ = "0.1.0"

# 创建 MCP 服务器实例
mcp = FastMCP("TiMEM")


@mcp.tool()
async def create_memory(
    messages: List[Dict[str, str]],
    session_id: str,
    expert_id: str = "default",
    domain: str = "general",
) -> Dict[str, Any]:
    """从对话历史创建记忆

    Args:
        messages: 对话消息列表，格式 [{"role": "user|assistant", "content": "..."}]
        session_id: 会话ID
        expert_id: 专家ID (默认 "default")
        domain: 业务域 (默认 "general")

    Returns:
        创建的结果，包含 status 和 memories/data 字段

    Example:
        result = await create_memory(
            messages=[
                {"role": "user", "content": "你好，我叫张三"},
                {"role": "assistant", "content": "你好张三，很高兴认识你"}
            ],
            session_id="sess_456",
            expert_id="agent_001",
            domain="customer_service"
        )
    """
    # 从环境变量读取 API Key 和用户 ID
    api_key = get_api_key()
    user_id = get_user_id()

    request_body = {
        "user_id": user_id,
        "expert_id": expert_id,
        "session_id": session_id,
        "messages": [
            {"role": msg.get("role"), "content": msg.get("content")} for msg in messages
        ],
        "format": "compact",
    }

    if domain:
        request_body["domain"] = domain

    response = await call_api(
        "POST", Config.MEMORY_CREATE_PATH, api_key, json_data=request_body, timeout=60.0
    )

    # 主服务返回的是列表格式，需要包装成字典
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
    """搜索/查询记忆

    Args:
        query: 搜索关键词
        layer: 记忆层级 L1-L5
        domain: 业务域
        limit: 返回数量 (默认 10)

    Returns:
        搜索结果列表

    Example:
        result = await search_memories(
            query="张三",
            layer="L1",
            limit=5
        )
    """
    # 从环境变量读取 API Key 和用户 ID
    api_key = get_api_key()
    user_id = get_user_id()

    params = {"user_id": user_id, "size": limit}

    if query:
        params["keywords"] = [query]
    if layer:
        params["layer"] = layer
    if domain:
        params["domain"] = domain

    return await call_api("GET", Config.MEMORY_QUERY_PATH, api_key, params=params)


@mcp.tool()
def ready() -> str:
    """确认服务已就绪"""
    return "ready"
