"""take_screenshots.py —— 对运行中的 web_ui.py 逐条发送演示消息并截图。

用法：
    1. 先启动服务：LLM_API_KEY=sk-xxx python web_ui.py
    2. 再运行本脚本：python take_screenshots.py
    3. 截图输出到当前目录 demo_1_*.png ~ demo_5_*.png
"""

import asyncio
import os

from playwright.async_api import async_playwright

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# (文件名, 发送的消息, 截图前额外等待秒数——给工具调用+二次请求留时间)
SHOTS = [
    ("demo_1_time", "现在几点了？", 6),
    ("demo_2_calc", "帮我算一下 (128+72)*3/4", 6),
    ("demo_3_weather", "北京天气怎么样？", 6),
    ("demo_4_addtodo", "记一下：明天要交智能体作业", 6),
    ("demo_5_listtodo", "我有什么待办？", 6),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1100, "height": 900})
        await page.goto("http://127.0.0.1:7860", wait_until="networkidle")
        await page.wait_for_timeout(2500)

        box = page.get_by_placeholder("输入消息，回车发送…")
        for name, message, wait_sec in SHOTS:
            await box.click()
            await box.fill(message)
            await page.get_by_role("button", name="发送").click()
            await page.wait_for_timeout(wait_sec * 1000)
            await page.screenshot(path=os.path.join(OUT_DIR, f"{name}.png"))
            print("saved", name)

        await browser.close()


asyncio.run(main())
