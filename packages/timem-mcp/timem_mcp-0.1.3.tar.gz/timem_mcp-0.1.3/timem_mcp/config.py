"""TiMEM MCP Configuration Module

Reads configuration from environment variables, supports both TiMEM_* and TIMEM_* prefixes.
Priority: TiMEM_* > TIMEM_*
"""

import os
from typing import Optional


class Config:
    """Configuration management class"""

    # Environment variable prefixes
    PREFIXES = ["TiMEM_", "TIMEM_"]

    # API paths
    MEMORY_CREATE_PATH = "/api/v1/memory/"
    MEMORY_QUERY_PATH = "/api/v1/memory/search"

    # Default API base URL
    DEFAULT_BASE_URL = "https://api.timem.cloud"

    @classmethod
    def _get_env(cls, key: str) -> Optional[str]:
        """Get environment variable with multiple prefix support

        Args:
            key: Configuration key (without prefix)

        Returns:
            Environment variable value, or None if not found
        """
        # Try different prefixes in priority order
        for prefix in cls.PREFIXES:
            value = os.getenv(f"{prefix}{key}")
            if value:
                return value
        return None

    @classmethod
    def get_api_key(cls) -> str:
        """Get API Key (required)"""
        api_key = cls._get_env("API_KEY")
        if not api_key:
            raise ValueError(
                "TiMEM_API_KEY environment variable is not set. "
                "Please set TiMEM_API_KEY or TIMEM_API_KEY in environment variables"
            )
        return api_key


    @classmethod
    def get_user_id(cls) -> Optional[str]:
        """Get User ID (optional)"""
        return cls._get_env("USER_ID")

    @classmethod
    def get_base_url(cls) -> str:
        """Get API base URL"""
        return cls._get_env("API_HOST") or cls.DEFAULT_BASE_URL

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        cls.get_api_key()


# Export convenient access functions
get_api_key = Config.get_api_key
get_user_id = Config.get_user_id
get_base_url = Config.get_base_url
validate = Config.validate
