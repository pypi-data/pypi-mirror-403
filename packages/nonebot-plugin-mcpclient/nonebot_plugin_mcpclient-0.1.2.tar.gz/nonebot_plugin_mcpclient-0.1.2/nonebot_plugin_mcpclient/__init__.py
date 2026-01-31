"""NoneBot2 MCP Client Plugin.

提供 MCP (Model Context Protocol) 客户端能力，允许连接多个 MCP 服务器，
获取并调用 MCP 工具，以 OpenAI function calling 格式暴露给其他插件使用。
"""

from typing import Any

from nonebot import get_driver, logger, require
from nonebot.plugin import PluginMetadata, get_plugin_config, inherit_supported_adapters

# 确保依赖的插件已加载
require("nonebot_plugin_alconna")

from .client import MCPClient
from .config import Config, MCPServerConfig

# 导入命令模块以注册命令
from . import commands  # noqa: F401

__version__ = "0.1.2"

__plugin_meta__ = PluginMetadata(
    name="MCP Client",
    description="NoneBot2 MCP 客户端插件，提供 MCP 工具调用能力",
    usage=(
        "API 使用:\n"
        "  from nonebot_plugin_mcpclient import get_mcp_tools, call_mcp_tool\n"
        "  tools = await get_mcp_tools()\n"
        "  result = await call_mcp_tool('mcp__server__tool', {...})\n\n"
        "命令使用:\n"
        "  /mcp <server> <tool> [args] - 调用 MCP 工具"
    ),
    type="library",
    homepage="https://github.com/gsskk/nonebot-plugin-mcpclient",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
)

_driver = get_driver()
_client = MCPClient.get_instance()


@_driver.on_startup
async def _startup() -> None:
    """启动时加载配置并初始化工具缓存."""
    try:
        config = get_plugin_config(Config)
        _client.configure(config.mcp_servers, config.mcp_tool_timeout)

        if config.mcp_servers:
            await _client.init_tools_cache()
        else:
            logger.info("[MCP] 未配置 MCP 服务器")
    except Exception as e:
        logger.error(f"[MCP] 初始化失败: {e}")


# ============ 对外 API ============


async def get_mcp_tools(user_id: str | None = None) -> list[dict[str, Any]]:
    """获取所有 MCP 工具 (OpenAI function calling 格式).

    Args:
        user_id: 用户 Session ID，用于权限过滤 (可选)

    Returns:
        工具列表，每个工具包含 type, function.name, function.description, function.parameters
    """
    from .permission import filter_tools_by_permission

    tools = await _client.get_tools()
    return filter_tools_by_permission(tools, user_id)


async def call_mcp_tool(
    tool_name: str,
    args: dict[str, Any],
    timeout: float | None = None,
    user_id: str | None = None,
) -> str:
    """调用 MCP 工具.

    Args:
        tool_name: 工具名，格式为 mcp__server__tool
        args: 工具参数字典
        timeout: 超时时间（秒），默认使用配置值
        user_id: 用户 Session ID，用于权限校验 (可选)

    Returns:
        工具调用结果字符串
    """
    from .permission import check_server_permission

    # 解析 server name 进行权限检查
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 2:
            server_name = parts[1]
            config = _client._server_config.get(server_name)
            if config and config.allowed_users and user_id:
                if not check_server_permission(server_name, user_id):
                    logger.warning(f"[MCP] Permission denied: {user_id} -> {tool_name}")
                    return f"权限不足：您无权访问 {server_name} 服务器"

    return await _client.call_tool(tool_name, args, timeout)


def is_mcp_tool(tool_name: str) -> bool:
    """判断是否为 MCP 工具.

    Args:
        tool_name: 工具名

    Returns:
        如果是 MCP 工具返回 True
    """
    return tool_name.startswith("mcp__")


def clear_mcp_cache() -> None:
    """清除工具缓存，用于热加载配置."""
    _client.clear_cache()


# Re-export for convenience
__all__ = [
    "__version__",
    "__plugin_meta__",
    "get_mcp_tools",
    "call_mcp_tool",
    "is_mcp_tool",
    "clear_mcp_cache",
    "MCPClient",
    "Config",
    "MCPServerConfig",
]

logger.info(f"[MCP] Plugin loaded: v{__version__}")
