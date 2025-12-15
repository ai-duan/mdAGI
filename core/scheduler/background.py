"""后台调度器"""
import datetime
import threading
import os

IDLE_TIMEOUT_SECONDS = int(os.getenv("AGI_IDLE_TIMEOUT_SEC", "30"))
IDLE_CHECK_INTERVAL = 5


class BackgroundScheduler:
    """后台任务调度器 - 空闲检测和自省"""
    
    def __init__(self, on_idle_callback=None):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_interaction = datetime.datetime.now()
        self._on_idle = on_idle_callback
    
    def start(self):
        """启动后台监控"""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止后台监控"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
    
    def note_interaction(self):
        """记录交互时间"""
        self._last_interaction = datetime.datetime.now()
    
    def _worker(self):
        """后台工作线程"""
        while not self._stop_event.wait(IDLE_CHECK_INTERVAL):
            idle_seconds = (datetime.datetime.now() - self._last_interaction).total_seconds()
            
            if idle_seconds >= IDLE_TIMEOUT_SECONDS and self._on_idle:
                self._on_idle()
                self.note_interaction()
