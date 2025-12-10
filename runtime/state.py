import dataclasses
from typing import List, Dict, Optional


@dataclasses.dataclass
class TodoItem:
    content: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, DONE


@dataclasses.dataclass
class AgentState:
    agent: Dict[str, str] = dataclasses.field(default_factory=dict)
    knowledge: List[str] = dataclasses.field(default_factory=list)
    memory: List[str] = dataclasses.field(default_factory=list)
    code: List[str] = dataclasses.field(default_factory=list)
    todo: List[TodoItem] = dataclasses.field(default_factory=list)

    def next_pending_todo(self) -> Optional[TodoItem]:
        for item in self.todo:
            if item.status == "PENDING":
                return item
        return None

    def mark_done(self, content: str):
        for item in self.todo:
            if item.content == content:
                item.status = "DONE"
                break
