"""内置工具"""
import os
from .registry import ToolRegistry, default_registry


def read_file(path: str) -> str:
    """读取文件"""
    print(f"[Tool] Reading {path}...")
    if not os.path.exists(path):
        return "Error: File not found."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    """写入文件"""
    print(f"[Tool] Writing to {path}...")
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "File written successfully."


def create_folder(path: str) -> str:
    """创建文件夹"""
    print(f"[Tool] Creating folder {path}...")
    if os.path.exists(path):
        return f"Folder already exists: {path}"
    os.makedirs(path)
    return f"Folder created successfully: {path}"


def register_builtins(registry: ToolRegistry = None):
    """注册所有内置工具"""
    reg = registry or default_registry
    
    reg.register(
        name="read_file",
        description="读取文件内容",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"}
            },
            "required": ["path"]
        },
        handler=read_file,
        modifies_state=False
    )
    
    reg.register(
        name="write_file",
        description="写入文件内容。用于创建或修改文件。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（需包含扩展名）"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["path", "content"]
        },
        handler=write_file,
        modifies_state=True
    )
    
    reg.register(
        name="create_folder",
        description="创建文件夹",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件夹路径"}
            },
            "required": ["path"]
        },
        handler=create_folder,
        modifies_state=True
    )
