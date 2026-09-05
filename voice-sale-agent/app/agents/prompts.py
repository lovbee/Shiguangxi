"""从资源目录读取并缓存 Prompt 文本。"""

from pathlib import Path


class PromptLoader:
    """按相对路径懒加载 UTF-8 Prompt，同一进程内只读磁盘一次。"""

    def __init__(self, base_dir: Path | None = None):
        """设置资源根目录；测试可传临时目录替代真实 Prompt。"""
        self.base_dir = base_dir or Path(__file__).resolve().parents[1] / "resources"
        self._cache: dict[str, str] = {}

    def load(self, relative_path: str) -> str:
        """返回 Prompt 内容；首次读取后放入内存字典缓存。"""
        if relative_path not in self._cache:
            self._cache[relative_path] = (self.base_dir / relative_path).read_text(encoding="utf-8")
        return self._cache[relative_path]
