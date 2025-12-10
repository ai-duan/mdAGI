import datetime
from .parser import parse_md, dump_state
from .llm import SimpleLLM
from .executor import execute_tool

# Memory 配置常量
MEMORY_LIMIT = 100  # 记忆库容量上限
KEEP_COUNT = 3  # 蒸馏后保留的记忆条数
MAX_MEMORY_LENGTH = 100  # 单条记忆最大字符数


class AgentRuntime:
    def __init__(self, md_file):
        self.file = md_file
        self.llm = SimpleLLM()
        self.reload()

    def reload(self):
        with open(self.file, "r", encoding="utf-8") as f:
            content = f.read()
        self.state = parse_md(content)

    def save(self):
        new_content = dump_state(self.state)
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[System] State saved to {self.file}")

    def run_once(self):
        print("\n=== 生命循环开始 (Life Loop Start) ===")

        # --- 1. 感知 (Perceive) ---
        self.reload()
        current_task = self.state.next_pending_todo()
        if not current_task:
            print("没有待办任务。进入休眠。")
            return

        print(f"当前任务: {current_task.content}")

        # Contextual Memory Retrieval (Simple limitation for now)
        recent_memories = self.state.memory[-10:]
        print(f"检索到 {len(recent_memories)} 条近期记忆。")

        # --- 2. 规划 (Plan) ---
        plan = self.llm.generate(
            agent=self.state.agent,
            knowledge=self.state.knowledge,
            memory=recent_memories,
            task=current_task,
            tools=["read_file", "write_file", "add_task"],
        )

        print(f"思考 (Thought): {plan.thought}")
        if plan.tool_call:
            print(f"计划工具 (Tool): {plan.tool_call.name}")

        # --- 3. 行动 (Act) ---
        result = None
        action_log = ""

        if plan.tool_call:
            try:
                if plan.tool_call.name == "add_task":
                    # Special internal action
                    new_task_content = plan.tool_call.args.get("task")

                    # Prevent infinite recursion (Decomposing task into itself)
                    if new_task_content.strip() == current_task.content.strip():
                        result = "错误: 不能将任务分解为它自己。请直接执行该任务 (例如使用 write_file)。"
                        action_log = "尝试无效分解 (递归阻断)"
                        # Do NOT mark current task as done.
                    else:
                        from .state import TodoItem

                        self.state.todo.append(
                            TodoItem(content=new_task_content, status="PENDING")
                        )
                        result = f"任务已添加: {new_task_content}"

                        # If we successfully decomposed, the parent task is technically "done" (or at least processed)
                        self.state.mark_done(current_task.content)
                        action_log = f"分解为: {new_task_content}"

                elif plan.tool_call.name == "mitosis":
                    # --- AGI CELL DIVISION (Mitosis) ---
                    child_name = plan.tool_call.args.get("child_name")
                    child_objective = plan.tool_call.args.get("objective")

                    # Create Child DNA
                    child_filename = f"{child_name}.md"
                    child_dna = f"""<agent>
name: {child_name}
objective: {child_objective}
parent: {self.state.agent.get('name', 'Origin')}
style: Focused, specialized.
</agent>

<knowledge>
[继承公理]
- 结构：agent, knowledge, memory, code, todo。
[父辈智慧]
{chr(10).join(self.state.knowledge)}
</knowledge>

<memory>
[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 我诞生于有丝分裂。我的使命是: {child_objective}
</memory>

<code>
# Inherited Runtime
</code>

<todo>
? 分析我的目标并规划第一步。
</todo>
"""
                    # Write to disk
                    with open(child_filename, "w", encoding="utf-8") as f:
                        f.write(child_dna)

                    result = (
                        f"分裂成功。子体 '{child_name}' 已创建于 '{child_filename}'。"
                    )
                    action_log = f"创造生命: {child_name}"
                    self.state.mark_done(current_task.content)

                elif plan.tool_call.name == "merge_child":
                    # --- AGI MERGE (Re-absorption) ---
                    child_file = plan.tool_call.args.get("child_file")
                    import os

                    try:
                        with open(child_file, "r", encoding="utf-8") as f:
                            c_content = f.read()
                        c_state = parse_md(c_content)

                        # 1. Absorb Knowledge (Uniquely)
                        new_know = 0
                        for k in c_state.knowledge:
                            if (
                                k not in self.state.knowledge
                                and "[父辈智慧]" not in k
                                and "[继承公理]" not in k
                                and "[Parental Wisdom]" not in k
                            ):
                                self.state.knowledge.append(k)
                                new_know += 1

                        # 2. Absorb Key Memory/Result (Last 3 memories)
                        last_mems = c_state.memory[-3:] if c_state.memory else []
                        for m in last_mems:
                            self.state.memory.append(f"[来自 {child_file}] {m}")

                        # 3. Cleanup
                        os.remove(child_file)

                        result = f"融合成功。子体 '{child_file}' 已吸收 (+{new_know} 条公理) 并删除。"
                        action_log = f"融合并删除: {child_file}"
                        self.state.mark_done(current_task.content)

                    except FileNotFoundError:
                        result = f"融合失败: 找不到子体文件 '{child_file}'。"
                        action_log = "融合失败"

                else:
                    # External action
                    result = execute_tool(plan.tool_call)
                    action_log = f"调用 {plan.tool_call.name} -> {result}"

                    # 更智能的任务完成判断:
                    # - read_file 只是读取,不算完成任务
                    # - write_file, create_folder 等实际修改操作才算完成
                    # - 如果有错误,不标记完成
                    if "Error" not in str(result):
                        # 只有实际修改操作才标记任务完成
                        if plan.tool_call.name in ["write_file", "create_folder"]:
                            self.state.mark_done(current_task.content)
                        # read_file 不标记完成,让Agent继续处理

            except Exception as e:
                result = f"执行错误: {str(e)}"
                action_log = f"调用 {plan.tool_call.name} 失败: {e}"
        else:
            # Pure thought / Final Answer
            result = plan.final_answer or "未采取行动。"
            action_log = f"思考: {plan.thought}"
            if plan.final_answer and "DONE" in plan.final_answer:
                self.state.mark_done(current_task.content)

        print(f"执行结果: {result}")

        # --- 4. 记忆 (Memorize) ---
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 调用LLM生成精简的记忆摘要
        memory_summary = self.llm.summarize_memory(
            task=current_task.content,
            thought=plan.thought,
            action=action_log,
            result=str(result),
        )
        # 记录格式: [时间戳] LLM生成的摘要
        memory_entry = f"[{timestamp}] {memory_summary}"

        self.state.memory.append(memory_entry)

        # --- 5. 沉淀 (Distill) ---
        if len(self.state.memory) > MEMORY_LIMIT:
            print(f"\n[系统] 记忆库容量 ({MEMORY_LIMIT}) 超限。启动知识蒸馏...")

            # Keep the last KEEP_COUNT memories
            memories_to_distill = self.state.memory[:-KEEP_COUNT]
            active_memory = self.state.memory[-KEEP_COUNT:]

            if memories_to_distill:
                new_insights = self.llm.distill_knowledge(memories_to_distill)
                print(f"[系统] 提炼出 {len(new_insights)} 条新智慧:")
                for insight in new_insights:
                    print(f"  + {insight}")
                    self.state.knowledge.append(f"[经验] {insight}")

                self.state.memory = active_memory
                print(f"[系统] 记忆库已截断。保留最后 {KEEP_COUNT} 条。")

        # Save to Disk (Persist Epigenetics)
        self.save()
        print("=== 生命循环结束 (End) ===\n")


if __name__ == "__main__":
    runtime = AgentRuntime("genesis_v1.md")
    # Run twice to clear the first two default tasks
    runtime.run_once()
    runtime.run_once()
