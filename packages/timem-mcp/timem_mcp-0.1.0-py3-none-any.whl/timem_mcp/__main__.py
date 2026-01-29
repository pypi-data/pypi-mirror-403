"""TiMEM MCP 服务入口点

支持通过 `uvx timem-mcp` 或 `python -m timem_mcp` 启动服务
"""

import sys

from .config import validate
from .server import mcp


def main() -> None:
    """主入口函数"""
    try:
        # 验证必需的环境变量
        validate()
    except ValueError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 使用 stdio 传输方式启动服务（MCP 标准要求）
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
