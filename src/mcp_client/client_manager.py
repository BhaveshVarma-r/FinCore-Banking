"""
MCP Client Manager - calls MCP server functions directly
instead of spawning subprocesses for better reliability and speed.
"""
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


def call_tool_sync(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Call a tool on a specific MCP server directly.
    Imports the server module and calls the function directly
    for maximum reliability and speed.
    """
    try:
        if server_name == "core_banking":
            from src.mcp_servers import core_banking_server as server
        elif server_name == "credit":
            from src.mcp_servers import credit_server as server
        elif server_name == "fraud":
            from src.mcp_servers import fraud_server as server
        elif server_name == "compliance":
            from src.mcp_servers import compliance_server as server
        else:
            return {
                "success": False,
                "error": "server_not_found",
                "message": f"Unknown MCP server: {server_name}",
            }

        # Get the function from the server module
        func = getattr(server, tool_name, None)
        if func is None:
            return {
                "success": False,
                "error": "tool_not_found",
                "message": f"Tool '{tool_name}' not found in {server_name}",
            }

        # Call the function directly with arguments
        result = func(**arguments)

        logger.debug(
            "mcp_client.tool_called",
            server=server_name,
            tool=tool_name,
            success=result.get("success", False),
        )

        return result

    except Exception as e:
        logger.error(
            "mcp_client.call_failed",
            server=server_name,
            tool=tool_name,
            error=str(e),
        )
        return {
            "success": False,
            "error": "call_failed",
            "message": str(e),
        }