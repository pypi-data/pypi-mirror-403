"""Plugin configuration."""

from typing import Literal

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """单个 MCP 服务器配置.

    Attributes:
        type: 传输类型，"stdio" 或 "sse"
        command: stdio 模式的命令
        args: stdio 模式的命令参数
        env: stdio 模式的环境变量
        url: SSE 模式的 URL
        headers: SSE 模式的请求头
        friendly_name: 友好名称，用于日志显示
        description: 服务器描述
        enabled: 是否启用
    """

    type: Literal["stdio", "sse", "streamablehttp"] = "stdio"

    # stdio 模式
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    # sse 模式
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    # 通用
    friendly_name: str | None = None
    description: str | None = None
    enabled: bool = True

    # 权限控制 (可选)
    allowed_users: list[str] = Field(default_factory=list)


class Config(BaseModel):
    """插件全局配置.

    Attributes:
        mcp_servers: MCP 服务器配置字典，键为服务器 ID
        mcp_tool_timeout: 工具调用超时时间（秒）
        mcp_cache_ttl: 工具缓存过期时间（秒），0 表示不过期
    """

    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    mcp_tool_timeout: int = 30
    mcp_cache_ttl: int = 3600
