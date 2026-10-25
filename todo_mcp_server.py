"""
todo_mcp_server.py —— 能力层：把 tools.py 的工具暴露为一个标准 MCP Server。

思路（对齐参考项目）：
    tools.py 里都是普通 Python 函数，这里用官方 SDK 的 FastMCP 装饰器
    逐个注册成 MCP 工具，一个 @mcp.tool() 就是模型能"看见"的一个工具。
    业务逻辑零改动，只是加了一层标准协议外壳。

它可以被任何 MCP Client 挂载（本项目 agent.py、Claude Desktop、各类 IDE 等）：
    python todo_mcp_server.py            # 以 stdio 方式启动，供客户端拉起
"""

from mcp.server.fastmcp import FastMCP

import tools

mcp = FastMCP("xiaozhi-tools")


@mcp.tool()
def get_current_time() -> str:
    """获取当前的日期、时间和星期。"""
    return tools.get_current_time()


@mcp.tool()
def calculator(expression: str) -> str:
    """计算四则运算表达式，支持加减乘除和括号。"""
    return tools.calculator(expression)


@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的天气情况。"""
    return tools.get_weather(city)


@mcp.tool()
def add_todo(content: str) -> str:
    """添加一条待办事项。"""
    return tools.add_todo(content)


@mcp.tool()
def list_todos() -> str:
    """列出所有待办事项。"""
    return tools.list_todos()


@mcp.tool()
def finish_todo(todo_id: int) -> str:
    """按编号把某条待办标记为已完成。"""
    return tools.finish_todo(todo_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
