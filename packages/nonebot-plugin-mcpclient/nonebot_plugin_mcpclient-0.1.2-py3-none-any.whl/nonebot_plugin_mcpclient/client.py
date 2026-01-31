"""MCP Client - 核心实现."""

import asyncio
from contextlib import AsyncExitStack
from typing import Any

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from nonebot import logger

from .config import MCPServerConfig


class MCPClient:
    """MCP 客户端 - 单例模式.

    提供 MCP 服务器连接和工具调用能力。
    """

    _instance: "MCPClient | None" = None
    _initialized: bool = False

    def __new__(cls) -> "MCPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._server_config: dict[str, MCPServerConfig] = {}
        self._tools_cache: list[dict[str, Any]] = []
        self._cache_initialized: bool = False
        self._timeout: float = 30.0
        self._initialized = True

    def configure(
        self,
        servers: dict[str, MCPServerConfig],
        timeout: float = 30.0,
    ) -> None:
        """配置服务器列表.

        Args:
            servers: 服务器配置字典
            timeout: 工具调用超时时间
        """
        self._server_config = {k: v for k, v in servers.items() if v.enabled}
        self._timeout = timeout
        self._cache_initialized = False
        logger.info(f"[MCP] 配置了 {len(self._server_config)} 个服务器")

    @classmethod
    def get_instance(cls) -> "MCPClient":
        """获取单例实例."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _create_session(self, server_name: str, exit_stack: AsyncExitStack) -> ClientSession:
        """创建临时会话.

        Args:
            server_name: 服务器名称
            exit_stack: 用于管理资源的 AsyncExitStack

        Returns:
            已初始化的 ClientSession
        """
        config = self._server_config[server_name]

        if config.type == "stdio":
            if not config.command:
                raise ValueError(f"stdio 服务器 {server_name} 缺少 command")
            transport = await exit_stack.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=config.command,
                        args=config.args,
                        env=config.env if config.env else None,
                    )
                )
            )
        elif config.type == "sse":
            if not config.url:
                raise ValueError(f"sse 服务器 {server_name} 缺少 url")
            transport = await exit_stack.enter_async_context(sse_client(url=config.url, headers=config.headers))
        elif config.type == "streamablehttp":
            if not config.url:
                raise ValueError(f"streamablehttp 服务器 {server_name} 缺少 url")
            # 创建带有 headers 的 httpx client
            http_client = httpx.AsyncClient(
                headers=config.headers or {},
                timeout=httpx.Timeout(self._timeout, read=300.0),
            )
            await exit_stack.enter_async_context(http_client)
            transport = await exit_stack.enter_async_context(
                streamable_http_client(url=config.url, http_client=http_client)
            )
        else:
            raise ValueError(f"不支持的传输类型: {config.type}")

        # streamable_http_client 返回 3 个值 (read, write, get_session_id)
        # sse_client 和 stdio_client 返回 2 个值 (read, write)
        if config.type == "streamablehttp":
            read, write, _get_session_id = transport
        else:
            read, write = transport
        session = await exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        return session

    async def init_tools_cache(self) -> None:
        """初始化工具列表缓存."""
        if self._cache_initialized:
            return

        tools: list[dict[str, Any]] = []

        for server_name, config in self._server_config.items():
            try:
                logger.info(f"[MCP] 正在连接服务器 {server_name} ...")
                async with AsyncExitStack() as stack:
                    # 连接和初始化增加超时
                    session = await asyncio.wait_for(self._create_session(server_name, stack), timeout=self._timeout)

                    logger.info(f"[MCP] 服务器 {server_name} 连接成功，正在获取工具列表...")
                    response = await asyncio.wait_for(session.list_tools(), timeout=self._timeout)

                    for tool in response.tools:
                        tool_full_name = f"mcp__{server_name}__{tool.name}"
                        tool_desc = tool.description or f"MCP tool: {tool.name}"
                        logger.debug(f"[MCP]   - {tool.name}: {tool_desc[:80]}")
                        tools.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool_full_name,
                                    "description": tool_desc,
                                    "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                                },
                            }
                        )

                    friendly = config.friendly_name or server_name
                    logger.info(f"[MCP] 从 {friendly} 加载了 {len(response.tools)} 个工具")
            except asyncio.TimeoutError:
                friendly = config.friendly_name or server_name
                logger.error(f"[MCP] 连接服务器 {friendly} 超时 ({self._timeout}s)，可能是协议不兼容或网络问题")
            except Exception:
                friendly = config.friendly_name or server_name
                logger.exception(f"[MCP] 连接服务器 {friendly} 失败")

        self._tools_cache = tools
        self._cache_initialized = True
        logger.info(f"[MCP] 工具缓存完成，共 {len(tools)} 个工具")

    async def get_tools(self) -> list[dict[str, Any]]:
        """获取所有工具 (OpenAI function calling 格式).

        Returns:
            工具列表
        """
        await self.init_tools_cache()
        return self._tools_cache.copy()

    def _parse_tool_name(self, tool_name: str) -> tuple[str, str]:
        """解析工具名.

        Args:
            tool_name: 工具名，格式为 mcp__server__tool

        Returns:
            (server_name, real_tool_name) 元组

        Raises:
            ValueError: 工具名格式无效
        """
        parts = tool_name.split("__")
        if len(parts) != 3 or parts[0] != "mcp":
            raise ValueError(f"无效的 MCP 工具名: {tool_name}")
        return parts[1], parts[2]

    async def call_tool(
        self,
        tool_name: str,
        args: dict[str, Any],
        timeout: float | None = None,
    ) -> str:
        """调用工具.

        Args:
            tool_name: 工具名，格式为 mcp__server__tool
            args: 工具参数
            timeout: 超时时间，默认使用配置值

        Returns:
            工具调用结果字符串
        """
        server_name, real_tool_name = self._parse_tool_name(tool_name)

        if server_name not in self._server_config:
            return f"未知的 MCP 服务器: {server_name}"

        config = self._server_config[server_name]
        friendly = config.friendly_name or server_name
        logger.info(f"[MCP] 调用 {friendly}.{real_tool_name}")

        effective_timeout = timeout if timeout is not None else self._timeout

        try:
            async with AsyncExitStack() as stack:
                session = await self._create_session(server_name, stack)
                response = await asyncio.wait_for(
                    session.call_tool(real_tool_name, args),
                    timeout=effective_timeout,
                )

                # 提取结果
                if response.content:
                    first = response.content[0]
                    if hasattr(first, "text"):
                        return first.text
                    return str(first)
                return "工具调用成功，无返回内容"
        except asyncio.TimeoutError:
            logger.warning(f"[MCP] 工具 {tool_name} 调用超时")
            return f"工具调用超时 ({effective_timeout}s)"
        except Exception as e:
            logger.error(f"[MCP] 工具 {tool_name} 调用失败: {e}")
            return f"工具调用失败: {e}"

    def clear_cache(self) -> None:
        """清除工具缓存."""
        self._tools_cache = []
        self._cache_initialized = False
        logger.info("[MCP] 工具缓存已清除")

    @property
    def server_count(self) -> int:
        """已配置的服务器数量."""
        return len(self._server_config)

    @property
    def tool_count(self) -> int:
        """已缓存的工具数量."""
        return len(self._tools_cache)
