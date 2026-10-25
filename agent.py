"""
agent.py —— 能说会做的智能体（主程序）

"会说"：调用大模型 API 进行多轮对话；
"会做"：通过工具调用执行真实动作，两种模式可切换：
    MCP=1        通过 MCP 协议调用（本模块 -> MCP Client -> MCP Server -> tools.py）
    未设置       进程内直接调用 tools.py（Function Calling 直连模式，便于对照原理）

使用前配置（任选一家 OpenAI 兼容接口即可，如 DeepSeek / 智谱 / Kimi / 通义）：
    export LLM_API_KEY="你的 API Key"
    export LLM_BASE_URL="https://api.deepseek.com/v1"   # 可选，默认 DeepSeek
    export LLM_MODEL="deepseek-chat"                     # 可选

运行：
    python agent.py
"""

import json
import os
import sys

from openai import OpenAI

import mcp_client
import tools

# ---------------- 配置 ----------------
API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
USE_MCP = os.environ.get("MCP", "") == "1"      # 是否走 MCP 协议调用工具
_mcp: "mcp_client.McpToolClient | None" = None

SYSTEM_PROMPT = (
    "你是课程作业《构建一个能说会做的智能体》中的助手小智。"
    "你不仅会聊天，还能调用工具帮用户做事情：查时间、做计算、查天气、管理待办清单。"
    "当用户的问题需要事实信息或具体动作时，请优先调用合适的工具，"
    "并根据工具返回的结果用简洁的中文回答；闲聊时正常对话即可。"
)


def create_client():
    if not API_KEY:
        print(
            "[提示] 未设置环境变量 LLM_API_KEY，无法连接大模型。\n"
            "        请先执行：export LLM_API_KEY=\"你的Key\"（Windows 用 set 或 $env:）\n"
            "        支持任意 OpenAI 兼容接口（DeepSeek / 智谱 / Kimi / 通义等）。"
        )
        sys.exit(1)
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def get_mcp_client() -> "mcp_client.McpToolClient":
    """懒加载 MCP Client（第一次用到时才拉起 Server 进程）。"""
    global _mcp
    if _mcp is None:
        _mcp = mcp_client.McpToolClient()
    return _mcp


def get_tools_schema() -> list:
    """取工具清单：MCP 模式由 tools/list 动态发现，直连模式用本地 JSON Schema。"""
    return get_mcp_client().list_tools() if USE_MCP else tools.TOOLS_SCHEMA


def run_tool_call(tool_call, verbose: bool = True) -> dict:
    """执行一次工具调用，返回符合协议的 tool 消息。"""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")
    try:
        if USE_MCP:
            # MCP 模式：tools/call 经 JSON-RPC 交给 Server 进程执行
            result = get_mcp_client().call_tool(name, args)
        else:
            func = tools.TOOL_FUNCTIONS.get(name)
            result = f"未知工具：{name}" if func is None else str(func(**args))
    except Exception as e:
        result = f"工具执行出错：{e}"
    if verbose:
        print(f"    🔧 [调用工具] {name}({args}) -> {result.splitlines()[0]}")
    return {"role": "tool", "tool_call_id": tool_call.id, "content": result}


def chat_once(client, messages: list, verbose: bool = True) -> str:
    """完成一轮对话：发给大模型 -> 需要时执行工具 -> 把结果回传 -> 生成最终回答。"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=get_tools_schema(),
    )
    msg = resp.choices[0].message

    # 模型决定调用工具
    if msg.tool_calls:
        messages.append(
            {"role": "assistant", "content": msg.content or "", "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name,
                              "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]}
        )
        for tc in msg.tool_calls:
            messages.append(run_tool_call(tc, verbose=verbose))
        # 把工具结果再交给模型，得到面向用户的最终回答
        resp = client.chat.completions.create(model=MODEL, messages=messages)
        msg = resp.choices[0].message

    reply = msg.content or ""
    messages.append({"role": "assistant", "content": reply})
    return reply


def main():
    client = create_client()
    # messages 里带 system 的历史，就是"多轮对话记忆"的实现方式
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 56)
    mode = "MCP 协议" if USE_MCP else "Function Calling 直连"
    print(f"  小智 · 能说会做的智能体｜工具调用模式：{mode}")
    print("  （输入 exit 退出，输入 clear 清空记忆）")
    print("=" * 56)
    while True:
        try:
            user_input = input("\n你 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("再见！")
            break
        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("（对话记忆已清空）")
            continue

        messages.append({"role": "user", "content": user_input})
        reply = chat_once(client, messages)
        print(f"\n小智 > {reply}")


if __name__ == "__main__":
    main()
