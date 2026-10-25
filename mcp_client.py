"""
mcp_client.py —— 调度层：作为 MCP Client 连接 MCP Server。

职责：
    1. 用 stdio 拉起 todo_mcp_server.py（JSON-RPC over 标准输入输出）；
    2. 握手 initialize()；
    3. tools/list 发现工具 -> 转换成 OpenAI Function Calling 需要的 schema；
    4. tools/call 调用工具 -> 取回文本结果。

两个工程细节：
    * MCP 官方 SDK 是 async 的，而对话循环是同步的（input / print），
      所以把事件循环放到后台线程；
    * anyio 的 cancel scope 要求"进入和退出在同一个任务里"，
      因此不能每次调用都新建任务，而是起一个常驻协程 _serve()，
      所有请求通过 asyncio.Queue 投递给它串行执行。
"""

import asyncio
import concurrent.futures
import os
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SERVER = os.path.join(BASE_DIR, "todo_mcp_server.py")


class McpToolClient:
    """一个极简 MCP Client：够用、能讲清楚原理。"""

    def __init__(self, server_script: str | None = None):
        self.server_script = server_script or DEFAULT_SERVER
        self.session = None
        self._ready = threading.Event()
        self._error: Exception | None = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._serve(), self._loop)
        if not self._ready.wait(timeout=60):
            raise RuntimeError(f"MCP Server 连接超时：{self._error}")

    # ---------- 常驻协程：连接 + 串行处理请求 ----------
    async def _serve(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        self._queue: asyncio.Queue = asyncio.Queue()
        params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script],
            env=dict(os.environ),
        )
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()      # MCP 握手
                    self.session = session
                    self._ready.set()
                    while True:
                        job = await self._queue.get()
                        if job is None:             # 退出信号
                            break
                        coro_fn, fut = job
                        try:
                            fut.set_result(await coro_fn())
                        except Exception as e:      # noqa: BLE001
                            fut.set_exception(e)
        except Exception as e:                      # noqa: BLE001
            self._error = e
            self._ready.set()

    # ---------- 同步侧投递请求 ----------
    def _call(self, coro_fn, timeout=60):
        fut: concurrent.futures.Future = concurrent.futures.Future()
        asyncio.run_coroutine_threadsafe(self._queue.put((coro_fn, fut)), self._loop)
        return fut.result(timeout=timeout)

    # ---------- 对外：发现工具 ----------
    def list_tools(self) -> list[dict]:
        """tools/list：把 MCP 的工具定义转成大模型能吃的 Function Calling schema。"""
        result = self._call(lambda: self.session.list_tools(), timeout=30)
        schema = []
        for t in result.tools:
            schema.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
            })
        return schema

    # ---------- 对外：调用工具 ----------
    def call_tool(self, name: str, arguments: dict) -> str:
        """tools/call：通过 JSON-RPC 请求 Server 执行工具，取回文本结果。"""
        result = self._call(lambda: self.session.call_tool(name, arguments))
        texts = [c.text for c in result.content if getattr(c, "text", None)]
        return "\n".join(texts) if texts else str(result.content)

    # ---------- 关闭 ----------
    def close(self):
        try:
            asyncio.run_coroutine_threadsafe(self._queue.put(None), self._loop).result(timeout=10)
        except Exception:                            # noqa: BLE001
            pass
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
