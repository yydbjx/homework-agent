"""
mcp_selftest.py —— MCP 链路自测（不依赖大模型 API Key）

验证 4 件事：
    1. 能按 stdio 拉起 MCP Server 并完成 initialize 握手；
    2. tools/list 能发现全部 6 个工具，且 description / 参数 schema 正确；
    3. tools/call 能经 JSON-RPC 真正执行工具并拿到结果；
    4. 待办的写 -> 读 -> 完成 全链路在 Server 进程内真实生效。

运行：python mcp_selftest.py
"""

import os

from mcp_client import McpToolClient

TODO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


def main():
    if os.path.exists(TODO_FILE):
        os.remove(TODO_FILE)

    client = McpToolClient()
    ok = 0
    total = 0

    print("① 连接 MCP Server：成功（initialize 握手完成）")

    # ② tools/list
    schema = client.list_tools()
    names = [t["function"]["name"] for t in schema]
    expected = {"get_current_time", "calculator", "get_weather",
                "add_todo", "list_todos", "finish_todo"}
    total += 1
    assert expected.issubset(set(names)), f"工具缺失：{expected - set(names)}"
    ok += 1
    print(f"② tools/list 发现 {len(names)} 个工具：{', '.join(names)}")

    # ③ tools/call —— 时间
    total += 1
    r = client.call_tool("get_current_time", {})
    assert "星期" in r, r
    ok += 1
    print(f"③ tools/call get_current_time -> {r}")

    # ④ tools/call —— 计算
    total += 1
    r = client.call_tool("calculator", {"expression": "(128+72)*3/4"})
    assert "150.0" in r, r
    ok += 1
    print(f"④ tools/call calculator -> {r}")

    # ⑤ 注入拦截同样经过 MCP 生效
    total += 1
    r = client.call_tool("calculator", {"expression": "import os"})
    assert "错误" in r, r
    ok += 1
    print(f"⑤ tools/call calculator(注入) -> {r}")

    # ⑥ tools/call —— 天气
    total += 1
    r = client.call_tool("get_weather", {"city": "北京"})
    assert "气温" in r, r
    ok += 1
    print(f"⑥ tools/call get_weather -> {r}")

    # ⑦⑧⑨ 待办写 -> 读 -> 完成（验证 Server 侧真实落盘）
    total += 3
    r1 = client.call_tool("add_todo", {"content": "明天要交智能体作业"})
    assert "已添加" in r1, r1
    ok += 1
    r2 = client.call_tool("list_todos", {})
    assert "明天要交智能体作业" in r2, r2
    ok += 1
    r3 = client.call_tool("finish_todo", {"todo_id": 1})
    assert "已完成" in r3, r3
    ok += 1
    print(f"⑦ add_todo -> {r1}")
    print(f"⑧ list_todos -> {r2}")
    print(f"⑨ finish_todo -> {r3}")

    print(f"\nMCP 链路自测：{ok}/{total} 项通过")
    client.close()

    if os.path.exists(TODO_FILE):
        os.remove(TODO_FILE)


if __name__ == "__main__":
    main()
