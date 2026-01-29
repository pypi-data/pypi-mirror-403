"""TiMEM API 客户端模块

提供异步 HTTP 客户端用于调用 TiMEM Engine API
"""

from typing import Any, Dict, Optional

import httpx

from .config import get_base_url


async def call_api(
    method: str,
    path: str,
    api_key: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """通用 API 调用函数

    Args:
        method: HTTP 方法 (GET/POST)
        path: API 路径
        api_key: API Key
        json_data: JSON 请求体 (POST 时使用)
        params: URL 查询参数 (GET 时使用)
        timeout: 超时时间

    Returns:
        API 响应数据

    Raises:
        httpx.HTTPStatusError: API 请求失败
    """
    url = f"{get_base_url()}{path}"
    headers = {"X-API-Key": api_key}

    async with httpx.AsyncClient() as client:
        if method.upper() == "POST":
            response = await client.post(
                url, json=json_data, headers=headers, timeout=timeout
            )
        else:
            response = await client.get(
                url, params=params, headers=headers, timeout=timeout
            )

        response.raise_for_status()
        return response.json()
