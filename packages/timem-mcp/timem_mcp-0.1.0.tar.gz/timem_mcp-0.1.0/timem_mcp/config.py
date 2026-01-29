"""TiMEM MCP 配置模块

从环境变量读取配置，支持 TiMEM_* 和 TIMEM_* 两种前缀。
优先级: TiMEM_* > TIMEM_*
"""

import os
from typing import Optional


class Config:
    """配置管理类"""

    # 环境变量前缀
    PREFIXES = ["TiMEM_", "TIMEM_"]

    # API paths
    MEMORY_CREATE_PATH = "/api/v1/memory/"
    MEMORY_QUERY_PATH = "/api/v1/memory/query"

    # Default API base URL
    DEFAULT_BASE_URL = "https://api.timem.cloud"

    @classmethod
    def _get_env(cls, key: str) -> Optional[str]:
        """获取环境变量，支持多种前缀

        Args:
            key: 配置键名（不含前缀）

        Returns:
            环境变量值，如果不存在则返回 None
        """
        # 按优先级尝试不同前缀
        for prefix in cls.PREFIXES:
            value = os.getenv(f"{prefix}{key}")
            if value:
                return value
        return None

    @classmethod
    def get_api_key(cls) -> str:
        """获取 API Key（必需）"""
        api_key = cls._get_env("API_KEY")
        if not api_key:
            raise ValueError(
                "TiMEM_API_KEY 环境变量未设置。"
                "请在环境变量中设置 TiMEM_API_KEY 或 TIMEM_API_KEY"
            )
        return api_key

    @classmethod
    def get_user_id(cls) -> str:
        """获取用户 ID（必需）"""
        user_id = cls._get_env("USER_ID")
        if not user_id:
            raise ValueError(
                "TiMEM_USER_ID 环境变量未设置。"
                "请在环境变量中设置 TiMEM_USER_ID 或 TIMEM_USER_ID"
            )
        return user_id

    @classmethod
    def get_base_url(cls) -> str:
        """获取 API 基础地址"""
        return cls._get_env("API_HOST") or cls.DEFAULT_BASE_URL

    @classmethod
    def validate(cls) -> None:
        """验证必需的配置项"""
        cls.get_api_key()
        cls.get_user_id()


# 导出便捷访问函数
get_api_key = Config.get_api_key
get_user_id = Config.get_user_id
get_base_url = Config.get_base_url
validate = Config.validate
