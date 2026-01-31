"""MCP 命令暴露模块."""

from nonebot import logger
from nonebot.adapters import Bot, Event
from arclet.alconna import Alconna, Args, CommandMeta, Arparma, MultiVar
from nonebot_plugin_alconna import on_alconna, Match

from .permission import check_server_permission

mcp_cmd = Alconna(
    "mcp",
    Args["server", str]["tool", str]["args", MultiVar(str, "*")],
    meta=CommandMeta(
        description="调用 MCP 工具",
        usage="/mcp <server> <tool> [args...]",
        example="/mcp github search_issues nonebot2",
    ),
)

mcp_matcher = on_alconna(mcp_cmd, priority=10, block=True, use_cmd_start=True)

logger.debug(f"[MCP] Command registered: {mcp_cmd.path}")


def _get_user_session_id(bot: Bot, event: Event) -> str:
    """构造用户 Session ID.

    格式: {adapter}+{target}+{user_id} 或 {adapter}+private+{user_id}
    """
    adapter_name = bot.type.lower().replace(" ", "")
    user_id = event.get_user_id()

    # 尝试获取群/频道 ID
    session_id = getattr(event, "group_id", None) or getattr(event, "channel_id", None)

    if session_id:
        return f"{adapter_name}+{session_id}+{user_id}"
    else:
        return f"{adapter_name}+private+{user_id}"


@mcp_matcher.handle()
async def handle_mcp(
    bot: Bot,
    event: Event,
    result: Arparma,
    server: Match[str],
    tool: Match[str],
    args: Match[tuple[str, ...]],
) -> None:
    """处理 MCP 命令.

    用法: /mcp <server> <tool> [args...]
    示例: /mcp github search_issues nonebot2
    """
    if not server.available or not tool.available:
        await mcp_matcher.finish("用法: /mcp <server> <tool> [args]")

    server_name = server.result
    tool_name = tool.result
    tool_args_tuple = args.result if args.available else ()

    # 获取用户 Session ID
    user_id = _get_user_session_id(bot, event)

    # 权限检查
    if not check_server_permission(server_name, user_id):
        await mcp_matcher.finish(f"权限不足：您无权访问 {server_name} 服务器")

    # 将参数组合为单个字符串传递给工具
    tool_args_str = " ".join(tool_args_tuple) if tool_args_tuple else ""

    logger.debug(f"[MCP] Command: server={server_name}, tool={tool_name}, args={tool_args_str!r}, user={user_id}")

    # 使用模块级 API 调用工具
    from . import call_mcp_tool

    full_tool_name = f"mcp__{server_name}__{tool_name}"
    result_text = await call_mcp_tool(full_tool_name, {"input": tool_args_str}, user_id=user_id)

    await mcp_matcher.finish(result_text)
