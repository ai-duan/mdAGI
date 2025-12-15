"""数据模型定义"""
import dataclasses
from typing import List, Dict, Optional


@dataclasses.dataclass
class TodoItem:
    """待办任务项"""
    content: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, DONE, FAILED
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    action_history: List[str] = dataclasses.field(default_factory=list)  # 执行历史
    failure_reason: str = ""  # 失败原因


@dataclasses.dataclass
class AgentState:
    """Agent 状态"""
    agent: Dict[str, str] = dataclasses.field(default_factory=dict)
    knowledge: List[str] = dataclasses.field(default_factory=list)
    memory: List[str] = dataclasses.field(default_factory=list)
    code: List[str] = dataclasses.field(default_factory=list)
    todo: List[TodoItem] = dataclasses.field(default_factory=list)

    def next_pending_todo(self) -> Optional[TodoItem]:
        """获取下一个待处理任务"""
        for item in self.todo:
            if item.status == "PENDING":
                return item
        return None

    def mark_done(self, content: str):
        """标记任务完成"""
        for item in self.todo:
            if item.content == content:
                item.status = "DONE"
                break

    def mark_failed(self, content: str, reason: str):
        """标记任务失败"""
        for item in self.todo:
            if item.content == content:
                item.status = "FAILED"
                item.failure_reason = reason
                break

    def increment_retry(self, content: str) -> int:
        """增加重试计数，返回当前重试次数"""
        for item in self.todo:
            if item.content == content:
                item.retry_count += 1
                return item.retry_count
        return 0

    def add_action_history(self, content: str, action: str):
        """添加执行历史"""
        for item in self.todo:
            if item.content == content:
                item.action_history.append(action)
                break

    def get_task(self, content: str) -> Optional[TodoItem]:
        """获取指定任务"""
        for item in self.todo:
            if item.content == content:
                return item
        return None
