"""TiMEM API Client Module

Provides async HTTP client for calling TiMEM Engine API
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
    """Generic API call function

    Args:
        method: HTTP method (GET/POST)
        path: API path
        api_key: API Key
        json_data: JSON request body (used for POST)
        params: URL query parameters (used for GET)
        timeout: Request timeout

    Returns:
        API response data

    Raises:
        httpx.HTTPStatusError: API request failed
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
