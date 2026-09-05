"""数据访问层包。

Repository 只封装 PostgreSQL/Redis 的读写，不负责 Agent 决策和用户话术。
业务层通过这些类访问数据，便于测试时替换成 Fake。
"""
