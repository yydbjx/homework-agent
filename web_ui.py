"""
web_ui.py —— 小智的网页界面（Gradio 版）

在命令行版基础上提供一个可在浏览器演示的聊天界面，并带"快捷指令"按钮，
方便截图放进博客随笔的功能演示部分。

运行：
    pip install gradio openai
    export LLM_API_KEY="你的Key"
    python web_ui.py
然后浏览器打开终端提示的地址（默认 http://127.0.0.1:7860）。
"""

import json
import os
import re

import gradio as gr

from agent import SYSTEM_PROMPT, MODEL, create_client, chat_once
import tools

# 离线演示模式：设置环境变量 MOCK=1 启动。
# 说明：此模式下"模型决策"由脚本模拟，但所有工具执行（时间/计算/天气/待办文件读写）
# 都是真实调用 tools.py，适合没有 API Key 时的课堂演示与截图。
MOCK = os.environ.get("MOCK", "") == "1"

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]


def mock_reply(message: str) -> str:
    """离线演示模式的回复：按关键词选择工具，执行是真的。"""
    m = message

    def call(name, args, result):
        return f"🔧 [调用工具] {name}({args})\n\n{result}"

    if "几点" in m or "时间" in m:
        return call("get_current_time", "{}", tools.get_current_time())
    if "天气" in m:
        city = next((c for c in CITIES if c in m), "北京")
        return call("get_weather", json.dumps({"city": city}, ensure_ascii=False),
                    tools.get_weather(city))
    if "待办" in m or "没做的事" in m or "记了什么" in m:
        return call("list_todos", "{}", tools.list_todos())
    if "记一下" in m or "记个" in m:
        content = re.split("[：:]", m, 1)[-1].strip() or m
        return call("add_todo", json.dumps({"content": content}, ensure_ascii=False),
                    tools.add_todo(content))
    if "完成" in m:
        num = re.search(r"\d+", m)
        if num:
            return call("finish_todo", json.dumps({"todo_id": int(num.group())}),
                        tools.finish_todo(int(num.group())))
    expr = re.search(r"[0-9(][0-9+\-*/().\s]*[0-9)]", m)
    if expr:
        e = expr.group()
        return call("calculator", json.dumps({"expression": e}), tools.calculator(e))
    return "（离线演示模式）我是小智，试试：现在几点了？/ 帮我算一下 (128+72)*3/4 / 北京天气怎么样？/ 记一下：… / 我有什么待办？"

# 快捷指令按钮（对应工具能力，方便演示）
QUICK_PROMPTS = [
    ["现在几点了？"],
    ["帮我算一下 (128+72)*3/4"],
    ["北京天气怎么样？"],
    ["记一下：明天要交智能体作业"],
    ["我有什么待办？"],
]

# 每个浏览器会话独立一份对话记忆
client = None if MOCK else create_client()


def respond(message, history):
    # Gradio 6 的 Chatbot 要求返回完整历史（messages 格式）
    history = list(history or [])
    history.append({"role": "user", "content": message})
    try:
        if MOCK:
            reply = mock_reply(message)
        else:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            reply = chat_once(client, messages, verbose=False)
    except Exception as e:
        reply = f"出错了：{e}\n请检查 API Key / 网络配置。"
    history.append({"role": "assistant", "content": reply})
    return history, ""


with gr.Blocks(title="小智 · 能说会做的智能体") as demo:
    gr.Markdown(
        "# 🤖 小智 · 能说会做的智能体\n"
        + (f"课程作业演示（模型：`{MODEL}`）—— 会聊天，也能查时间、算数、查天气、管待办。"
           if not MOCK else
           "课程作业演示（**离线演示模式**：工具执行为真实运行，模型决策由脚本模拟）"
           "—— 会聊天，也能查时间、算数、查天气、管待办。")
    )
    chatbot = gr.Chatbot(height=420,
                         label="对话窗口（支持多轮记忆）")
    msg = gr.Textbox(placeholder="输入消息，回车发送…", label="你的消息")
    with gr.Row():
        send_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.Button("🧹 清空记忆")
    gr.Examples(QUICK_PROMPTS, inputs=msg, label="快捷指令")

    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    send_btn.click(respond, [msg, chatbot], [chatbot, msg])
    clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])


if __name__ == "__main__":
    demo.launch()
