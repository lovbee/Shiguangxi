"""Alembic 运行环境。

业务运行使用 SQLAlchemy ``asyncpg`` URL，而 Alembic 当前以同步引擎执行，
所以这里把驱动替换成 psycopg。``Base.metadata`` 仅包含已映射 ORM 表，
自动生成迁移前仍要注意完整 schema.sql 中尚未映射的表和向量列。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.models.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """不连接数据库，只根据 URL 生成可执行 SQL。"""
    url = get_settings().database_url.replace("+asyncpg", "+psycopg")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """建立一次同步连接并直接把迁移应用到目标数据库。"""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_settings().database_url.replace("+asyncpg", "+psycopg")
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# Alembic 根据命令参数选择 ``--sql`` 离线模式或真实在线迁移。
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
