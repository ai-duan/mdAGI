"""Agent 主类 - 对外统一接口"""
import os
from .state import StateStore
from .mind import LLMClient
from .loop import LifeLoop
from .scheduler import BackgroundScheduler


class Agent:
    """
    Genesis Agent - AGI 运行时
    整合状态、认知、工具、调度的统一接口
    """
    
    def __init__(
        self,
        dna_file: str,
        mode: str = "foreground",
        start_background: bool = True
    ):
        self.dna_file = dna_file
        self.mode = mode
        
        # 初始化组件
        self.store = StateStore(dna_file)
        self.llm = LLMClient()
        self.meta_prompt = self._load_meta_prompt() if mode in ["background", "dual"] else None
        
        # 生命循环
        self.loop = LifeLoop(
            store=self.store,
            llm=self.llm,
            meta_prompt=self.meta_prompt
        )
        
        # 后台调度
        self.scheduler = BackgroundScheduler(on_idle_callback=self._on_idle)
        if start_background and mode in ["dual", "background"]:
            self.scheduler.start()
        
        # 加载初始状态
        self.store.load()
    
    def _load_meta_prompt(self) -> str | None:
        """加载系统提示词"""
        path = ".ai/meta.md"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                print("[Agent] 已加载 meta.md")
                return f.read()
        return None
    
    def _on_idle(self):
        """空闲时触发自省"""
        print("[Agent] 空闲，触发自省...")
        try:
            wake_agent = Agent(".ai/wake.md", mode="background", start_background=False)
            wake_agent.run_once()
        except Exception as e:
            print(f"[Agent] 自省失败: {e}")
    
    @property
    def state(self):
        """获取当前状态"""
        return self.store.state
    
    def reload(self):
        """重新加载状态"""
        self.store.load()
    
    def save(self):
        """保存状态"""
        self.store.save()
    
    def run_once(self) -> bool:
        """执行一次生命循环（处理一个任务）"""
        self.scheduler.note_interaction()
        return self.loop.run_once()
    
    def run_all(self, on_progress=None) -> dict:
        """执行所有待办任务，直到全部完成"""
        self.scheduler.note_interaction()
        return self.loop.run_all(on_progress)
    
    def request_stop(self):
        """请求停止执行"""
        self.loop.request_stop()
    
    def note_interaction(self, reason: str = "interaction"):
        """记录交互"""
        self.scheduler.note_interaction()
    
    def stop(self):
        """停止 Agent"""
        self.loop.request_stop()
        self.scheduler.stop()
