"""
tools.py —— 智能体的"手"：让它不仅能说，还能做。

每个工具就是一个普通的 Python 函数，
通过 FUNCTIONS 里的 JSON Schema 描述告诉大模型"你有哪些工具可以调用"。
"""

import json
import os
import re
from datetime import datetime

# 待办事项持久化文件（保存在当前目录）
TODO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


# ---------- 工具 1：查询当前时间 ----------
def get_current_time() -> str:
    """获取当前的日期和时间。"""
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return now.strftime("%Y-%m-%d %H:%M:%S") + " " + weekdays[now.weekday()]


# ---------- 工具 2：数学计算器 ----------
def calculator(expression: str) -> str:
    """计算一个四则运算表达式的结果，例如 (3+5)*12/2。"""
    # 只允许数字、运算符和括号，防止执行任意代码
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        return "错误：只能计算包含数字和 + - * / ( ) 的算式"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错：{e}"


# ---------- 工具 3：查询天气（模拟数据，避免依赖外部 API Key） ----------
MOCK_WEATHER = {
    "北京": ("晴", 18, "微风"),
    "上海": ("多云", 22, "东南风 3 级"),
    "广州": ("小雨", 27, "南风 2 级"),
    "深圳": ("阴", 26, "东风 2 级"),
    "杭州": ("晴转多云", 21, "微风"),
    "成都": ("阴天", 17, "北风 1 级"),
    "武汉": ("晴", 20, "南风 2 级"),
    "西安": ("多云", 16, "东北风 2 级"),
}


def get_weather(city: str) -> str:
    """查询某个城市的天气（教学用模拟数据）。"""
    info = MOCK_WEATHER.get(city.strip())
    if info is None:
        return f"暂无「{city}」的天气数据（示例支持：{'、'.join(MOCK_WEATHER)}）"
    weather, temp, wind = info
    return f"{city}：{weather}，气温 {temp}℃，{wind}"


# ---------- 工具 4：待办事项管理 ----------
def _load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(content: str) -> str:
    """添加一条待办事项。"""
    todos = _load_todos()
    todos.append({"id": len(todos) + 1, "content": content, "done": False})
    _save_todos(todos)
    return f"已添加待办：{content}（当前共 {len(todos)} 条）"


def list_todos() -> str:
    """列出所有待办事项。"""
    todos = _load_todos()
    if not todos:
        return "当前没有待办事项。"
    lines = [f"[{'✓' if t['done'] else ' '}] {t['id']}. {t['content']}" for t in todos]
    return "\n".join(lines)


def finish_todo(todo_id: int) -> str:
    """按编号标记某条待办为已完成。"""
    todos = _load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            _save_todos(todos)
            return f"待办 {todo_id}「{t['content']}」已完成！"
    return f"找不到编号为 {todo_id} 的待办。"


# ---------- 工具注册表 ----------
# 函数名 -> 实际函数
TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculator": calculator,
    "get_weather": get_weather,
    "add_todo": add_todo,
    "list_todos": list_todos,
    "finish_todo": finish_todo,
}

# 告诉大模型有哪些工具可用的 JSON Schema（OpenAI function calling 格式）
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期、时间和星期",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算四则运算表达式，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "算式，如 (3+5)*12/2"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如 北京"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "添加一条待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "待办内容"}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "列出所有待办事项",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_todo",
            "description": "按编号把某条待办标记为已完成",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "待办编号"}
                },
                "required": ["todo_id"],
            },
        },
    },
]
