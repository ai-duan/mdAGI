"""
UI Service Layer for Genesis Agent.

Provides the business logic interface between the Gradio UI and the core Agent system.
"""

import os
import sys
import threading
from dataclasses import dataclass
from typing import Generator

from core.agent import Agent
from core.parser.aml import parse_aml
from ui.logger import UILogCapture
from ui.errors import safe_execute, safe_execute_generator, format_error


@dataclass
class TaskFileInfo:
    """Information about a task file in the work directory."""
    path: str
    name: str
    pending_count: int


@dataclass
class RunConfig:
    """Configuration for running an Agent."""
    file: str
    mode: str
    loop: int


@dataclass
class AgentStateView:
    """View model for Agent state display."""
    agent_name: str
    todo_list: list[dict]
    memory: list[str]
    is_running: bool


class AgentUIService:
    """Service layer for Agent UI operations."""
    
    WORK_DIR = "work"
    
    def __init__(self):
        self.current_agent: Agent | None = None
        self.is_running: bool = False
        self._stop_requested: bool = False
        self._lock = threading.Lock()
    
    @safe_execute_generator("运行 Agent")
    def run_agent(self, file: str, mode: str) -> Generator[str, None, None]:
        """Run Agent and yield log output.
        
        Creates an Agent instance and executes ALL tasks until completion.
        Agent will automatically retry failed tasks (max 3 times) and
        create follow-up tasks for unfinished work.
        
        Args:
            file: Path to the DNA file.
            mode: Run mode - 'foreground', 'background', or 'dual'.
            
        Yields:
            Log output strings during execution.
        """
        # Validate inputs
        if not file or not os.path.isfile(file):
            yield f"❌ 文件未找到: {file}"
            return
        
        if mode not in ("foreground", "background", "dual"):
            yield f"❌ 无效的运行模式: {mode}"
            return
        
        # Set up log capture
        log_capture = UILogCapture()
        log_buffer = []
        
        def on_progress(msg: str):
            """进度回调，收集日志"""
            log_buffer.append(msg)
        
        with self._lock:
            self._stop_requested = False
            self.is_running = True
        
        try:
            yield f"🚀 启动 Agent: {file}"
            yield f"   模式: {mode}"
            yield "   Agent 将自动执行所有任务直到完成"
            yield ""
            
            # Create Agent instance
            start_background = mode in ("background", "dual")
            
            with log_capture:
                self.current_agent = Agent(
                    dna_file=file,
                    mode=mode,
                    start_background=start_background
                )
            
            # Yield any logs from Agent initialization
            init_logs = log_capture.get_logs()
            if init_logs:
                yield init_logs
            log_capture.clear()
            
            # Execute ALL tasks
            with log_capture:
                stats = self.current_agent.run_all(on_progress=on_progress)
            
            # Yield captured logs
            run_logs = log_capture.get_logs()
            if run_logs:
                yield run_logs
            
            # Yield progress logs
            for log_line in log_buffer:
                yield log_line
            
            yield f"\n✅ Agent 运行完成"
            yield f"   完成: {stats['completed']}, 失败: {stats['failed']}, 总计: {stats['total']}"
            
        except FileNotFoundError as e:
            yield f"❌ 文件未找到: {e}"
        except Exception as e:
            yield f"❌ 错误: {type(e).__name__}: {e}"
        finally:
            # Clean up
            with self._lock:
                if self.current_agent:
                    self.current_agent.stop()
                self.current_agent = None
                self.is_running = False
                self._stop_requested = False
    
    @safe_execute("停止 Agent")
    def stop_agent(self) -> str:
        """Stop the currently running Agent.
        
        Gracefully terminates the running Agent by setting a stop flag
        and saving the current state before stopping.
        
        Returns:
            Status message indicating the result of the stop operation.
        """
        with self._lock:
            if not self.is_running or self.current_agent is None:
                return "⚠️ 没有正在运行的 Agent"
            
            self._stop_requested = True
            
            # Save state before stopping
            self.current_agent.save()
            
            return "⏹️ 已请求停止 Agent"
    
    def list_task_files(self) -> list[TaskFileInfo]:
        """List task files from the work/ directory.
        
        Scans the work directory for lowercase .md files and extracts
        Agent name and pending task count from each file.
        
        Returns:
            List of TaskFileInfo with path, name, and pending_count.
        """
        result: list[TaskFileInfo] = []
        
        if not os.path.isdir(self.WORK_DIR):
            return result
        
        for filename in os.listdir(self.WORK_DIR):
            # Only process lowercase .md files
            if not filename.endswith(".md"):
                continue
            if filename != filename.lower():
                continue
            
            filepath = os.path.join(self.WORK_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                state = parse_aml(content)
                agent_name = state.agent.get("name", filename)
                pending_count = sum(1 for item in state.todo if item.status == "PENDING")
                
                result.append(TaskFileInfo(
                    path=filepath,
                    name=agent_name,
                    pending_count=pending_count
                ))
            except Exception as e:
                # Log error but continue with other files
                # Include file with error indicator
                result.append(TaskFileInfo(
                    path=filepath,
                    name=f"⚠️ {filename} (解析错误)",
                    pending_count=0
                ))
                continue
        
        return result
    
    @safe_execute("添加任务")
    def add_task(self, task_content: str, file: str | None = None) -> str:
        """Add a task to the current Agent's todo list.
        
        Adds a new task with PENDING status to the Agent's todo list
        and persists it to the DNA file immediately.
        
        Args:
            task_content: The task description to add.
            file: Path to the DNA file. If None, uses current_agent's file.
            
        Returns:
            Status message indicating success or failure.
        """
        # Validate task content
        if not task_content or not task_content.strip():
            return "❌ 任务内容不能为空"
        
        task_content = task_content.strip()
        
        # Determine which file to use
        target_file = file
        if not target_file and self.current_agent:
            target_file = self.current_agent.dna_file
        
        if not target_file:
            return "❌ 没有指定 DNA 文件，请先选择一个文件"
        
        if not os.path.isfile(target_file):
            raise FileNotFoundError(target_file)
        
        # Load current state from file
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        state = parse_aml(content)
        
        # Add new task with PENDING status
        from core.state.models import TodoItem
        new_task = TodoItem(content=task_content, status="PENDING")
        state.todo.append(new_task)
        
        # Persist to file immediately
        from core.parser.aml import dump_aml
        new_content = dump_aml(state)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        # If current agent is using this file, reload its state
        if self.current_agent and self.current_agent.dna_file == target_file:
            self.current_agent.reload()
        
        return f"✅ 任务已添加: {task_content}"
    
    @safe_execute_generator("批量处理")
    def batch_process(self) -> Generator[str, None, None]:
        """Batch process all task files in the work directory.
        
        Processes all task files sequentially, continuing on individual
        file failures and yielding progress updates.
        
        Yields:
            Progress and status messages for each file being processed.
        """
        # Get list of task files
        task_files = self.list_task_files()
        
        if not task_files:
            yield "⚠️ work/ 目录中没有找到任务文件"
            return
        
        total = len(task_files)
        success_count = 0
        failure_count = 0
        
        yield f"🚀 开始批量处理 {total} 个任务文件\n"
        
        for i, task_file in enumerate(task_files, 1):
            yield f"\n--- [{i}/{total}] 处理: {task_file.name} ---"
            yield f"   文件: {task_file.path}"
            yield f"   待办任务: {task_file.pending_count}"
            
            if task_file.pending_count == 0:
                yield "   ⏭️ 没有待办任务，跳过"
                continue
            
            try:
                # Create Agent for this file and run once
                log_capture = UILogCapture()
                
                with log_capture:
                    agent = Agent(
                        dna_file=task_file.path,
                        mode="foreground",
                        start_background=False
                    )
                
                # Yield initialization logs
                init_logs = log_capture.get_logs()
                if init_logs:
                    yield init_logs
                log_capture.clear()
                
                # Run one cycle for each pending task
                tasks_processed = 0
                while tasks_processed < task_file.pending_count:
                    with log_capture:
                        has_task = agent.run_once()
                    
                    # Yield execution logs
                    run_logs = log_capture.get_logs()
                    if run_logs:
                        yield run_logs
                    log_capture.clear()
                    
                    if not has_task:
                        break
                    
                    tasks_processed += 1
                
                # Clean up
                agent.stop()
                
                yield f"   ✅ 完成处理 {task_file.name}"
                success_count += 1
                
            except Exception as e:
                yield f"   ❌ 处理失败: {type(e).__name__}: {e}"
                failure_count += 1
                # Continue with next file - don't stop on failure
                continue
        
        # Summary
        yield f"\n{'='*40}"
        yield f"📊 批量处理完成"
        yield f"   成功: {success_count}"
        yield f"   失败: {failure_count}"
        yield f"   跳过: {total - success_count - failure_count}"
    
    def get_agent_state(self, file: str) -> AgentStateView | str:
        """Get the current state of an Agent from its DNA file.
        
        Loads and parses the DNA file to extract the Agent's current state
        including todo list and memory.
        
        Args:
            file: Path to the DNA file.
            
        Returns:
            AgentStateView with agent name, todo list, memory, and running status.
            Returns error string if the file cannot be loaded or parsed.
        """
        if not file:
            return "⚠️ 请选择一个 DNA 文件"
        
        if not os.path.isfile(file):
            return f"❌ 文件未找到: {file}"
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            
            state = parse_aml(content)
            agent_name = state.agent.get("name", os.path.basename(file))
            
            # Convert todo items to dict format for display
            todo_list = [
                {"content": item.content, "status": item.status}
                for item in state.todo
            ]
            
            return AgentStateView(
                agent_name=agent_name,
                todo_list=todo_list,
                memory=state.memory,
                is_running=self.is_running
            )
        except Exception as e:
            return format_error(e, "加载 Agent 状态")
