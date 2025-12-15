"""配置加载工具"""
import os


def load_meta_prompt(path: str = ".ai/meta.md") -> str | None:
    """加载系统提示词"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None
