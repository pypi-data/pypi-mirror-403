# nonebot-plugin-mcpclient

NoneBot2 MCP (Model Context Protocol) 客户端插件，提供 MCP 工具调用能力。

该插件允许机器人连接多个 MCP 服务器，获取并调用 MCP 工具，并将工具以 OpenAI function calling 格式暴露给其他插件使用。

## 💿 安装

```bash
pip install nonebot-plugin-mcpclient
```

## ⚙️ 配置

在 `.env` 文件中添加以下配置：

```env
# MCP 服务器配置 (JSON 格式)
MCP_SERVERS='{
  "memory": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-memory"],
    "friendly_name": "长期记忆",
    "description": "跨会话的知识图谱记忆"
  },
  "github": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-github"],
    "env": {"GITHUB_TOKEN": "ghp_xxx"},
    "friendly_name": "GitHub"
  }
}'

# 工具调用超时 (秒)
MCP_TOOL_TIMEOUT=30

# 工具缓存过期时间 (秒), 0 表示不过期
MCP_CACHE_TTL=3600
```

### 服务器类型

#### stdio 模式

通过子进程的标准输入输出通信：

```json
{
  "github": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-github"],
    "env": {"GITHUB_TOKEN": "ghp_xxx"},
    "friendly_name": "GitHub"
  }
}
```

#### SSE 模式

通过 HTTP Server-Sent Events (GET 请求) 通信，适用于标准 MCP SSE 服务器：

```json
{
  "remote-server": {
    "type": "sse",
    "url": "https://mcp.example.com/sse",
    "headers": {"Authorization": "Bearer xxx"},
    "friendly_name": "远程服务器"
  }
}
```

#### Streamable HTTP 模式

通过 HTTP POST 请求通信，适用于支持 [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http) 协议的 MCP 服务器（如麦当劳 MCP）：

```json
{
  "mcd": {
    "type": "streamablehttp",
    "url": "https://mcp.mcd.cn/mcp-servers/mcd-mcp",
    "headers": {
      "Authorization": "Bearer YOUR_MCP_TOKEN"
    },
    "friendly_name": "麦当劳"
  }
}
```

> [!NOTE]
> **SSE vs Streamable HTTP**：
> - `sse`：使用 GET 请求建立 SSE 流，适用于大多数开源 MCP 服务器
> - `streamablehttp`：使用 POST 请求，支持双向通信，适用于企业级 MCP 服务（如麦当劳）

### 权限控制 (可选)

可以通过 `allowed_users` 字段限制 MCP 服务器只对特定用户可用，支持 fnmatch 通配符模式：

```json
{
  "mcd": {
    "type": "streamablehttp",
    "url": "https://mcp.mcd.cn/mcp-servers/mcd-mcp",
    "headers": {"Authorization": "Bearer xxx"},
    "friendly_name": "麦当劳",
    "allowed_users": [
      "onebotv11+private+123456789",
      "onebotv11+*+987654321",
      "discord+*"
    ]
  }
}
```

**Session ID 格式**：`{adapter}+{target}+{user_id}`
- 私聊：`onebotv11+private+123456789`
- 群聊：`onebotv11+123456+789012345`

**通配符示例**：
- `onebotv11+*+123456789` - 某用户在所有群/私聊
- `discord+*` - 所有 Discord 用户
- `*+*+123456789` - 跨适配器的特定用户

> [!TIP]
> 如果未配置 `allowed_users` 或配置为空列表，则所有用户都可访问（向后兼容）。

## 🎉 使用指南

### 命令调用

```
/mcp <server> <tool> [args...]
```

**示例：**
```
/mcp github search_issues nonebot2
/mcp memory save "用户偏好深色主题"
```

### API 调用

```python
from nonebot_plugin_mcpclient import get_mcp_tools, call_mcp_tool, is_mcp_tool

# 获取所有工具 (OpenAI function calling 格式)
tools = await get_mcp_tools()

# 调用工具
result = await call_mcp_tool("mcp__github__search_issues", {"query": "nonebot2"})

# 判断是否为 MCP 工具
if is_mcp_tool("mcp__github__search_issues"):
    print("这是一个 MCP 工具")
```

## 🔧 与 nonebot-plugin-dify 集成

本插件通过 `Plugin-as-a-Tool` 机制向 Dify 暴露能力。

### 1. 暴露的命令

插件暴露了一个统一入口命令：

```
/mcp <server> <tool> [args...]
```

对于麦当劳 MCP，命令示例：
- 查活动：`/mcp mcd campaign-calender`
- 查优惠券：`/mcp mcd available-coupons`

### 2. Dify 配置指南

为了让 nonebot-plugin-dify 的 LLM 知道如何使用这些工具，你需要在 `.env` 中配置 `TOOL_SCHEMA_OVERRIDE`，**显式告诉 LLM 有哪些服务器和工具可用**。

```env
TOOL_ENABLE=True
TOOL_ALLOWLIST='["mcp"]'
TOOL_SCHEMA_OVERRIDE='{
  "mcp": {
    "description": "调用 MCP 工具。支持以下服务器和能力：\n1. 麦当劳 (server: mcd)\n   - campaign-calender: 查询活动日历\n   - available-coupons: 查可领优惠券\n   - auto-bind-coupons: 一键领取所有券\n   - my-coupons: 查我的优惠券\n   - now-time-info: 获取当前时间\n\n2. GitHub (server: github)\n   - search_issues: 搜索 Issue\n   - read_file: 读取文件",
    "parameters": {
      "type": "object",
      "properties": {
        "server": {
          "type": "string",
          "description": "MCP 服务器名，例如：mcd, github",
          "enum": ["mcd", "github"]
        },
        "tool": {
          "type": "string",
          "description": "工具名称，例如：campaign-calender, available-coupons"
        },
        "args": {
          "type": "string",
          "description": "工具参数，视具体工具而定。无参数工具传空字符串。"
        }
      },
      "required": ["server", "tool"]
    },
    "format": "/mcp {server} {tool} {args}"
  }
}'
```

**关键点**：
- 在 `description` 中详细列出支持的 `server` 和 `tool`，这样 LLM 才能在用户问 "看看麦当劳有什么活动" 时，正确生成 `/mcp mcd campaign-calender` 的调用。
- `format` 字段指导 nonebot-plugin-dify 如何将 LLM 的意图转换为 NoneBot 命令。


## 许可证

MIT
