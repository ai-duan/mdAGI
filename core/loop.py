"""生命循环 - Agent 的核心执行逻辑"""
import datetime
from typing import Optional, Callable
from .state import AgentState, TodoItem, StateStore
from .mind import LLMClient, Planner, MemoryManager
from .tools import ToolRegistry, ToolExecutor, register_builtins


class LifeLoop:
    """
    生命循环 - 感知→规划→行动→记忆→沉淀
    
    两层循环结构：
    - 外层：遍历所有待办任务，直到全部完成
    - 内层：单个任务的多步执行 + 重试机制
    """
    
    MAX_STEPS_PER_TASK = 10  # 单个任务最大执行步数
    MAX_RETRIES = 3  # 单个任务最大重试次数
    
    def __init__(
        self,
        store: StateStore,
        llm: LLMClient,
        registry: ToolRegistry = None,
        meta_prompt: str = None
    ):
        self.store = store
        self.llm = llm
        self.meta_prompt = meta_prompt
        self._stop_requested = False
        
        # 初始化工具
        self.registry = registry or ToolRegistry()
        register_builtins(self.registry)
        self.executor = ToolExecutor(self.registry)
        
        # 初始化认知组件
        self.planner = Planner(llm, self.registry.get_schemas_for_llm())
        self.memory_mgr = MemoryManager(llm)
    
    def request_stop(self):
        """请求停止循环"""
        self._stop_requested = True
    
    def run_all(self, on_progress: Callable[[str], None] = None) -> dict:
        """
        执行所有待办任务，直到全部完成
        
        Args:
            on_progress: 进度回调函数，用于输出日志
            
        Returns:
            执行统计 {"completed": int, "failed": int, "total": int}
        """
        self._stop_requested = False
        stats = {"completed": 0, "failed": 0, "total": 0}
        
        def log(msg: str):
            print(msg)
            if on_progress:
                on_progress(msg)
        
        log("\n🚀 开始执行所有任务...")
        
        while not self._stop_requested:
            # 加载最新状态
            state = self.store.load()
            task = state.next_pending_todo()
            
            if not task:
                log("\n✅ 所有任务已完成！")
                break
            
            stats["total"] += 1
            log(f"\n{'='*50}")
            log(f"📋 任务 [{stats['total']}]: {task.content}")
            log(f"{'='*50}")
            
            # 执行单个任务（包含重试机制）
            success = self._execute_task_with_retry(task, log)
            
            if success:
                stats["completed"] += 1
            else:
                stats["failed"] += 1
        
        if self._stop_requested:
            log("\n⏹️ 收到停止请求，已终止")
        
        log(f"\n📊 执行统计: 完成 {stats['completed']}, 失败 {stats['failed']}, 总计 {stats['total']}")
        return stats

    def run_once(self) -> bool:
        """
        执行一次生命循环（兼容旧接口）
        只处理一个任务，但会完整执行该任务（多步+重试）
        
        Returns:
            是否有任务被执行
        """
        state = self.store.load()
        task = state.next_pending_todo()
        
        if not task:
            print("没有待办任务。")
            return False
        
        print(f"\n=== 执行任务: {task.content} ===")
        self._execute_task_with_retry(task, print)
        return True
    
    def _execute_task_with_retry(self, task: TodoItem, log: Callable) -> bool:
        """
        执行单个任务，包含重试机制
        
        Returns:
            任务是否成功完成
        """
        state = self.store.load()
        retry_count = 0
        
        while retry_count < self.MAX_RETRIES:
            if self._stop_requested:
                return False
            
            retry_count += 1
            log(f"\n--- 尝试 {retry_count}/{self.MAX_RETRIES} ---")
            
            # 执行任务的多个步骤
            success, all_actions, last_result = self._execute_task_steps(task, log)
            
            if success:
                # 任务成功完成
                state = self.store.load()
                state.mark_done(task.content)
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                summary = self.memory_mgr.summarize_action(
                    task=task.content,
                    thought=f"经过{len(all_actions)}步完成",
                    action="; ".join(all_actions[-3:]),
                    result="任务成功完成"
                )
                state.memory.append(f"[{timestamp}] ✓ {summary}")
                
                self._maybe_distill(state)
                self.store.save(state)
                
                log(f"\n✅ 任务完成: {task.content}")
                return True
            
            # 任务未完成，记录重试
            state = self.store.load()
            state.increment_retry(task.content)
            state.add_action_history(task.content, f"尝试{retry_count}未完成")
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state.memory.append(f"[{timestamp}] ⟳ 第{retry_count}次尝试未完成: {task.content}")
            self.store.save(state)
            
            if retry_count < self.MAX_RETRIES:
                log(f"⟳ 将进行第 {retry_count + 1} 次尝试...")
        
        # 达到最大重试次数，标记失败
        self._handle_task_failure(task, all_actions, last_result, log)
        return False

    def _execute_task_steps(self, task: TodoItem, log: Callable) -> tuple:
        """
        执行任务的多个步骤
        
        Returns:
            (success, all_actions, last_result)
        """
        state = self.store.load()
        all_actions = []
        last_result = ""
        
        for step in range(1, self.MAX_STEPS_PER_TASK + 1):
            if self._stop_requested:
                return False, all_actions, last_result
            
            log(f"\n  步骤 {step}/{self.MAX_STEPS_PER_TASK}")
            
            # 规划下一步
            plan = self.planner.plan(
                agent=state.agent,
                knowledge=state.knowledge,
                memory=state.memory[-10:] + all_actions[-5:],
                task=task.content,
                meta_prompt=self.meta_prompt
            )
            
            log(f"  思考: {plan.thought[:100]}")
            
            # 执行行动
            action_log, result_str = self._execute_action(state, task, plan)
            all_actions.append(action_log)
            last_result = result_str
            
            log(f"  结果: {result_str[:150]}")
            
            # 检查是否完成
            if plan.task_completed:
                return True, all_actions, last_result
            
            # 如果是 write_file 成功，检查任务是否完成
            if plan.tool_call and plan.tool_call.name == "write_file" and "Error" not in result_str:
                completion_check = self.planner.check_task_completion(
                    task=task.content,
                    action_history=all_actions,
                    last_result=result_str
                )
                log(f"  完成检查: {completion_check.get('reason', '')[:80]}")
                
                if completion_check.get("completed", False):
                    return True, all_actions, last_result
        
        # 达到最大步数仍未完成
        log(f"  ⚠️ 达到最大步数 {self.MAX_STEPS_PER_TASK}，任务未完成")
        return False, all_actions, last_result
    
    def _execute_action(self, state: AgentState, task: TodoItem, plan) -> tuple:
        """执行单个行动，返回 (action_log, result_str)"""
        action_log = ""
        result_str = ""
        
        if plan.tool_call:
            if plan.tool_call.name == "add_task":
                result_str = self._handle_add_task(state, task, plan.tool_call.args)
                action_log = f"add_task: {plan.tool_call.args}"
            else:
                result = self.executor.execute(plan.tool_call)
                result_str = str(result.output)
                action_log = f"{plan.tool_call.name}({plan.tool_call.args}) -> {result_str[:50]}"
        else:
            result_str = plan.final_answer or "无行动"
            action_log = f"思考: {plan.thought[:50]}"
        
        return action_log, result_str
    
    def _handle_add_task(self, state: AgentState, current: TodoItem, args: dict) -> str:
        """处理添加任务"""
        new_content = args.get("task", "")
        
        if new_content.strip() == current.content.strip():
            return "错误: 不能将任务分解为它自己"
        
        state.todo.append(TodoItem(content=new_content, status="PENDING"))
        self.store.save(state)
        return f"任务已添加: {new_content}"

    def _handle_task_failure(self, task: TodoItem, actions: list, last_result: str, log: Callable):
        """处理任务失败"""
        state = self.store.load()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 分析失败原因
        failure_analysis = self._analyze_failure(task.content, actions, last_result)
        
        # 标记任务失败
        failure_reason = f"重试{self.MAX_RETRIES}次后仍未完成"
        state.mark_failed(task.content, failure_reason)
        
        # 记录到记忆
        state.memory.append(f"[{timestamp}] ✗ 任务失败: {task.content}")
        state.memory.append(f"[{timestamp}] 失败分析: {failure_analysis}")
        
        # 创建后续任务
        followup_task = self._create_followup_task(task.content, actions, failure_analysis)
        if followup_task:
            state.todo.append(TodoItem(content=followup_task, status="PENDING"))
            log(f"\n→ 已创建后续任务: {followup_task}")
        
        self._maybe_distill(state)
        self.store.save(state)
        
        log(f"\n✗ 任务失败（重试{self.MAX_RETRIES}次）: {task.content}")
        log(f"  原因: {failure_analysis[:100]}")
    
    def _analyze_failure(self, task: str, actions: list, last_result: str) -> str:
        """分析失败原因"""
        actions_str = "\n".join(f"- {a}" for a in actions[-5:])
        
        prompt = f"""分析以下任务失败的原因：

任务: {task}

已执行的操作:
{actions_str}

最后结果: {last_result}

请简要分析（不超过100字）：
1. 失败原因
2. 缺少什么条件
3. 可能的解决方案"""

        messages = [{"role": "user", "content": prompt}]
        result = self.llm.chat(messages)
        
        if result:
            return result["choices"][0]["message"].get("content", "分析失败")[:200]
        return "无法分析失败原因"
    
    def _create_followup_task(self, original_task: str, actions: list, failure_analysis: str) -> str:
        """创建后续任务"""
        prompt = f"""原任务失败: {original_task}

失败分析: {failure_analysis}

请生成一个简短的后续任务描述，用于完成原任务未完成的部分。
只输出任务描述，不要其他内容（不超过50字）："""

        messages = [{"role": "user", "content": prompt}]
        result = self.llm.chat(messages)
        
        if result:
            followup = result["choices"][0]["message"].get("content", "").strip()
            if followup and followup != original_task:
                return f"[续] {followup[:50]}"
        return None
    
    def _maybe_distill(self, state: AgentState):
        """如果需要，执行记忆蒸馏"""
        if self.memory_mgr.should_distill(len(state.memory)):
            new_knowledge, active_memory = self.memory_mgr.distill(state.memory)
            state.knowledge.extend(new_knowledge)
            state.memory = active_memory
