"""
test_tools.py —— 不需要 API Key 也能验证工具集是否正常工作。
运行：python test_tools.py
"""

import tools

if __name__ == "__main__":
    print(tools.get_current_time())
    print(tools.calculator("(128+72)*3/4"))
    print(tools.calculator("import os"))          # 应被拦截
    print(tools.get_weather("北京"))
    print(tools.get_weather("火星"))
    print(tools.add_todo("明天要交智能体作业"))
    print(tools.list_todos())
    print(tools.finish_todo(1))
    print(tools.list_todos())
