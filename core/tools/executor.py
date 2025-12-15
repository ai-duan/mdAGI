"""工具执行器"""
import dataclasses
from typing import Any
from .registry import ToolRegistry, default_registry


@dataclasses.dataclass
class ToolCall:
    """工具调用"""
    name: str
    args: dict


@dataclasses.dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: Any
    modifies_state: bool = False


class ToolExecutor:
    """工具执行器 - 类似 OS 系统调用处理器"""
    
    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or default_registry
    
    def execute(self, call: ToolCall) -> ToolResult:
        """执行工具调用"""
        tool = self.registry.get(call.name)
        
        if not tool:
            return ToolResult(
                success=False,
                output=f"Unknown tool: {call.name}"
            )
        
        try:
            output = tool.handler(**call.args)
            return ToolResult(
                success="Error" not in str(output),
                output=output,
                modifies_state=tool.modifies_state
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error executing tool: {e}"
            )
