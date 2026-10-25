# 能说会做的智能体（课程作业）

《构建一个能说会做的智能体》作业的**最基本要求版**实现：

- **会说（对话）**：调用大模型 API（任意 OpenAI 兼容接口：DeepSeek / 智谱 / Kimi / 通义等），支持多轮对话记忆。
- **会做（行动）**：通过 Function Calling 调用真实工具——查时间、算数、查天气、管理待办清单。
- 不依赖任何 Agent 框架（L1 基础版），纯 Python 实现，便于理解 Agent 的本质原理。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `agent.py` | 主程序：对话循环、工具调用调度、多轮记忆 |
| `tools.py` | 工具集：6 个工具函数 + 告诉大模型的 JSON Schema |
| `todo_mcp_server.py` | MCP Server（FastMCP）：把 6 个工具按标准协议暴露 |
| `mcp_client.py` | MCP Client：stdio 连接、tools/list 发现、tools/call 调用 |
| `mcp_selftest.py` | MCP 链路自测：不依赖大模型 Key |
| `web_ui.py` | 网页界面（Gradio）：聊天窗口 + 快捷指令按钮 |
| `test_tools.py` | 自测脚本：无需 API Key 验证工具行为 |
| `todo.json` | 待办数据文件（运行后自动生成） |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（以 DeepSeek 为例）
export LLM_API_KEY="sk-你的Key"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
# Windows PowerShell:
# $env:LLM_API_KEY="sk-你的Key"

# 3a. 命令行版
python agent.py

# 3b. 网页版（浏览器打开 http://127.0.0.1:7860）
python web_ui.py

# 3c. 离线演示模式（无 API Key 也能演示：工具执行真实，模型决策脚本化）
MOCK=1 python web_ui.py
# Windows PowerShell: $env:MOCK="1"; python web_ui.py
```

## 使用示例

```text
你 > 现在几点了？
小智 > 现在是 2026-10-24 22:58:31 星期六。

你 > 帮我算一下 (128+72)*3/4
小智 > (128+72)*3/4 = 150.0

你 > 北京天气怎么样？
小智 > 北京：晴，气温 18℃，微风。

你 > 记一下：明天要交智能体作业
小智 > 已添加待办：明天要交智能体作业（当前共 1 条）

你 > 我有哪些没做的事？
小智 > [ ] 1. 明天要交智能体作业
```

运行效果中会打印 `🔧 [调用工具] ...` 的日志，展示 Agent "思考 → 调工具 → 回答"的完整过程。
