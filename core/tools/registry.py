"""工具注册表"""
from typing import Callable, Dict, Any, List
import dataclasses


@dataclasses.dataclass
class ToolSchema:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    modifies_state: bool = False  # 是否修改状态（用于判断任务完成）


class ToolRegistry:
    """工具注册表 - 类似 OS 系统调用表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        modifies_state: bool = False
    ):
        """注册工具"""
        self._tools[name] = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            modifies_state=modifies_state
        )
    
    def get(self, name: str) -> ToolSchema | None:
        """获取工具"""
        return self._tools.get(name)
    
    def list_names(self) -> List[str]:
        """列出所有工具名"""
        return list(self._tools.keys())
    
    def get_schemas_for_llm(self) -> List[Dict]:
        """生成 LLM 工具调用格式"""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schemas


# 全局注册表实例
default_registry = ToolRegistry()
