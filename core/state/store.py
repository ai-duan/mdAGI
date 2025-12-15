"""状态持久化"""
import threading
from .models import AgentState
from core.parser import parse_aml, dump_aml


class StateStore:
    """状态存储管理器"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._state: AgentState = None
    
    def load(self) -> AgentState:
        """从文件加载状态"""
        with self._lock:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self._state = parse_aml(content)
            return self._state
    
    def save(self, state: AgentState = None):
        """保存状态到文件"""
        with self._lock:
            if state:
                self._state = state
            content = dump_aml(self._state)
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"[Store] State saved to {self.filepath}")
    
    @property
    def state(self) -> AgentState:
        return self._state
