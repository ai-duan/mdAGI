"""
Error handling utilities for the Genesis Agent UI.

Provides decorators and utilities for consistent error handling
and message formatting across the UI service layer.
"""

import functools
from typing import Callable, TypeVar, ParamSpec, Generator, Any

P = ParamSpec('P')
T = TypeVar('T')


def format_error(error: Exception, context: str | None = None) -> str:
    """Format an error message with type and context information.
    
    Args:
        error: The exception that occurred.
        context: Optional context about what operation was being performed.
        
    Returns:
        Formatted error message string.
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"❌ {context}: {error_type}: {error_msg}"
    return f"❌ 错误: {error_type}: {error_msg}"


def safe_execute(context: str | None = None) -> Callable[[Callable[P, T]], Callable[P, T | str]]:
    """Decorator for safely executing service methods with error handling.
    
    Wraps a function to catch exceptions and return formatted error messages
    instead of raising. Useful for UI-facing methods where exceptions should
    be displayed to the user rather than crashing the application.
    
    Args:
        context: Optional context string describing the operation.
        
    Returns:
        Decorator function.
        
    Example:
        @safe_execute("添加任务")
        def add_task(self, content: str) -> str:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T | str]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | str:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                return f"❌ 文件未找到: {e}"
            except PermissionError as e:
                return f"❌ 权限不足: {e}"
            except ValueError as e:
                ctx = context or func.__name__
                return f"❌ {ctx}: 无效的值: {e}"
            except Exception as e:
                return format_error(e, context or func.__name__)
        return wrapper
    return decorator


def safe_execute_generator(context: str | None = None) -> Callable[
    [Callable[P, Generator[str, None, None]]], 
    Callable[P, Generator[str, None, None]]
]:
    """Decorator for safely executing generator methods with error handling.
    
    Similar to safe_execute but for generator functions that yield strings.
    Catches exceptions and yields formatted error messages.
    
    Args:
        context: Optional context string describing the operation.
        
    Returns:
        Decorator function.
        
    Example:
        @safe_execute_generator("运行 Agent")
        def run_agent(self, file: str) -> Generator[str, None, None]:
            ...
    """
    def decorator(
        func: Callable[P, Generator[str, None, None]]
    ) -> Callable[P, Generator[str, None, None]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Generator[str, None, None]:
            try:
                yield from func(*args, **kwargs)
            except FileNotFoundError as e:
                yield f"❌ 文件未找到: {e}"
            except PermissionError as e:
                yield f"❌ 权限不足: {e}"
            except ValueError as e:
                ctx = context or func.__name__
                yield f"❌ {ctx}: 无效的值: {e}"
            except Exception as e:
                yield format_error(e, context or func.__name__)
        return wrapper
    return decorator


class UIError(Exception):
    """Base exception for UI-related errors."""
    
    def __init__(self, message: str, context: str | None = None):
        self.context = context
        super().__init__(message)
    
    def format(self) -> str:
        """Format the error for display."""
        if self.context:
            return f"❌ {self.context}: {self}"
        return f"❌ {self}"


class AgentNotRunningError(UIError):
    """Raised when an operation requires a running Agent but none is active."""
    pass


class InvalidConfigError(UIError):
    """Raised when Agent configuration is invalid."""
    pass
