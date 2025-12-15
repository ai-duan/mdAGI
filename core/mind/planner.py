"""规划器 - 决策引擎"""
import dataclasses
import json
from typing import Optional, List, Dict
from .llm import LLMClient
from core.tools.executor import ToolCall


@dataclasses.dataclass
class Plan:
    """执行计划"""
    thought: str
    tool_call: Optional[ToolCall] = None
    final_answer: Optional[str] = None
    task_completed: bool = False  # 任务是否完成
    failure_reason: str = ""  # 失败原因


class Planner:
    """规划器 - 根据上下文生成执行计划"""
    
    def __init__(self, llm: LLMClient, tool_schemas: List[Dict]):
        self.llm = llm
        self.tool_schemas = tool_schemas
    
    def check_task_completion(
        self,
        task: str,
        action_history: List[str],
        last_result: str
    ) -> Dict[str, any]:
        """
        检查任务是否完成
        返回: {"completed": bool, "reason": str, "next_action": str}
        """
        if not action_history:
            return {"completed": False, "reason": "尚未执行任何操作", "next_action": "开始执行任务"}
        
        history_str = "\n".join(f"- {a}" for a in action_history[-5:])
        
        prompt = f"""判断以下任务是否已完成：

任务: {task}

已执行的操作:
{history_str}

最后一次操作结果: {last_result}

请分析并回答（JSON格式）:
{{
    "completed": true/false,
    "reason": "判断理由",
    "next_action": "如果未完成，下一步应该做什么"
}}
"""
        messages = [{"role": "user", "content": prompt}]
        result = self.llm.chat(messages)
        
        if not result:
            return {"completed": False, "reason": "LLM调用失败", "next_action": "重试"}
        
        content = result["choices"][0]["message"].get("content", "")
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 简单判断
        if "完成" in content or "成功" in content or "done" in content.lower():
            return {"completed": True, "reason": content, "next_action": ""}
        
        return {"completed": False, "reason": content, "next_action": "继续执行"}
    
    def plan(
        self,
        agent: Dict,
        knowledge: List[str],
        memory: List[str],
        task: str,
        meta_prompt: str = None
    ) -> Plan:
        """生成执行计划"""
        print(f"\n--- [Planner] 任务: {task} ---")
        
        # 构建系统提示词
        meta_section = f"[元层指导]\n{meta_prompt}\n---\n" if meta_prompt else ""
        
        system_prompt = f"""{meta_section}你是 {agent.get('name', 'Genesis AI')}。
目标: {agent.get('objective', 'Evolve')}
风格: {agent.get('style', 'Concise')}

[核心法则]
1. 先看记忆，不要重复失败的行动
2. 行动优先：创建文件用 write_file，创建文件夹用 create_folder
3. 修改文件直接用 write_file 写入新内容
4. 避免无效循环：读取后应该写入

[知识库]: {knowledge[-10:] if knowledge else []}
[记忆]: {memory[-10:] if memory else []}
"""

        user_prompt = f"当前任务: {task}\n决定下一步行动。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = self.llm.chat(messages, tools=self.tool_schemas)
        
        if not result:
            return Plan(thought="LLM 调用失败", final_answer="Error")
        
        message = result["choices"][0]["message"]
        content = message.get("content", "") or ""
        
        # 解析工具调用
        if message.get("tool_calls"):
            tool_data = message["tool_calls"][0]
            func_name = tool_data["function"]["name"]
            args = json.loads(tool_data["function"]["arguments"])
            
            return Plan(
                thought=f"调用 {func_name}，参数: {args}",
                tool_call=ToolCall(name=func_name, args=args)
            )
        
        # 检查是否明确表示完成
        is_done = "DONE" in content or "完成" in content or "已完成" in content
        
        return Plan(
            thought=content,
            final_answer=content if is_done else None,
            task_completed=is_done
        )
