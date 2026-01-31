"""Permission control for MCP servers."""

import fnmatch

from nonebot import logger

from .client import MCPClient


def check_server_permission(server_name: str, user_id: str | None) -> bool:
    """Check if user has permission to access the specified MCP server.

    Uses fnmatch for wildcard pattern matching against allowed_users.

    Args:
        server_name: The MCP server name
        user_id: User's full session ID (e.g., "onebotv11+private+123456789")

    Returns:
        True if user has permission, False otherwise
    """
    client = MCPClient.get_instance()
    config = client._server_config.get(server_name)

    if not config:
        return False  # Server not found

    allowed_users = config.allowed_users
    if not allowed_users:
        return True  # No restriction = open to all

    if not user_id:
        return False  # No user ID provided but restriction exists

    # Check if user matches any pattern
    for pattern in allowed_users:
        if fnmatch.fnmatch(user_id, pattern):
            logger.debug(f"[MCP] Permission granted: {user_id} matches {pattern}")
            return True

    logger.debug(f"[MCP] Permission denied: {user_id} not in allowed_users for {server_name}")
    return False


def filter_tools_by_permission(tools: list[dict], user_id: str | None) -> list[dict]:
    """Filter tools list based on user permission.

    Args:
        tools: List of tools in OpenAI function calling format
        user_id: User's full session ID

    Returns:
        Filtered list containing only tools the user can access
    """
    if not user_id:
        # If no user_id provided, return all tools (backward compatible)
        return tools

    client = MCPClient.get_instance()
    filtered = []

    for tool in tools:
        tool_name = tool.get("function", {}).get("name", "")
        if not tool_name.startswith("mcp__"):
            filtered.append(tool)
            continue

        # Parse server name from tool name: mcp__{server}__{tool}
        parts = tool_name.split("__")
        if len(parts) >= 2:
            server_name = parts[1]
            config = client._server_config.get(server_name)

            # If no allowed_users restriction, include the tool
            if not config or not config.allowed_users:
                filtered.append(tool)
                continue

            # Check permission
            if check_server_permission(server_name, user_id):
                filtered.append(tool)
        else:
            filtered.append(tool)

    return filtered
