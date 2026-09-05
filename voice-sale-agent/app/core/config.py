"""集中声明并读取应用配置。

Pydantic Settings 会把 ``.env``/系统环境变量转换成有类型的 Python 字段，
必填密钥缺失时让应用在启动阶段尽早失败，而不是运行到业务中途才报错。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用所有可配置项的唯一来源。

    字段名不区分环境变量大小写，例如 ``database_url`` 会读取
    ``DATABASE_URL``。``Field(...)`` 表示该项没有安全默认值，必须显式提供。
    """

    # 忽略旧部署环境中已移除的 JWT/CORS 变量，避免升级时因遗留 .env 无法启动。
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "voice-sale-agent"
    env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8010

    database_url: str = Field(...)
    database_ssl: bool = False
    redis_url: str = Field(...)

    dashscope_api_key: str = Field(...)
    llm_main_model: str = "qwen-max"
    llm_light_model: str = "qwen-turbo"
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024
    asr_model: str = "paraformer-realtime-v2"
    tts_model: str = "cosyvoice-v1"
    tts_voice: str = "longwan"

    session_ttl_minutes: int = 30
    agent_turn_lock_ttl_seconds: int = 180
    max_history_turns: int = 10
    perspective_enabled: bool = True

    @property
    def session_ttl_seconds(self) -> int:
        """把便于人工配置的分钟值转换成 Redis 需要的秒数。"""
        return self.session_ttl_minutes * 60

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回进程级配置单例，避免每次依赖注入都重新读取 ``.env``。"""
    return Settings()
