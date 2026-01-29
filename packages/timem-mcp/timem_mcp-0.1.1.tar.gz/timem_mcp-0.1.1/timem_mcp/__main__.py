"""TiMEM MCP Service Entry Point

Supports starting service via `uvx timem-mcp` or `python -m timem_mcp`
"""

import sys

from .config import validate
from .server import mcp


def main() -> None:
    """Main entry point"""
    try:
        # Validate required environment variables
        validate()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Start service using stdio transport (MCP standard requirement)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
