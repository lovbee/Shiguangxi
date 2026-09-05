"""应用包初始化。

这个文件在任何 ``app.*`` 模块被导入前执行。Windows 默认的 Proactor
事件循环与 psycopg 的异步连接池不兼容，因此只在 Windows 上切换策略；
Linux/macOS 保持系统默认值。
"""

import asyncio
import sys

if sys.platform == "win32":
    # 必须在数据库连接池创建前设置，否则 LangGraph 的 PostgreSQL
    # Checkpointer 可能在启动阶段报事件循环不兼容错误。
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
