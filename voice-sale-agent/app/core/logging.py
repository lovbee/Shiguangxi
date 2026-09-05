"""应用日志的最小统一配置。"""

import logging


def configure_logging(debug: bool = False) -> None:
    """根据调试开关设置根日志级别和通用文本格式。

    这里只调用标准库 ``basicConfig``；生产环境通常还会补充 JSON 格式、
    trace/session 字段和敏感信息脱敏。
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
