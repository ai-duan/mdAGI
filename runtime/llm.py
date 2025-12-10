import dataclasses
from typing import List, Optional, Dict, Any
import requests
import json


@dataclasses.dataclass
class ToolCall:
    name: str
    args: dict


@dataclasses.dataclass
class Plan:
    thought: str
    tool_call: Optional[ToolCall] = None
    final_answer: Optional[str] = None


class SimpleLLM:
    def __init__(
        self, base_url: str = "http://127.0.0.1:3000", model: str = "qwen/qwen3-vl-4b"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_url = f"{self.base_url}/v1/chat/completions"

    def _get_tool_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容。用于读取 Genesis 文件或其他任何文件。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "要读取的文件路径",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "向文件写入内容。用于创建新文件或更新现有文件。注意：此工具用于操作文件，不是文件夹。只有当任务涉及创建或修改带有扩展名的文件（如 .html, .js, .css, .txt 等）时才使用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "要写入的文件路径，必须包含文件扩展名（如 .html, .js, .css 等）",
                            },
                            "content": {
                                "type": "string",
                                "description": "要写入的内容",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "向待办列表添加新任务。用于将复杂任务分解为更小的子步骤。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "新任务的描述",
                            }
                        },
                        "required": ["task"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "mitosis",
                    "description": "创建一个新的子代 Agent（新的 .md 文件）来处理特定的宏大目标。这是‘细胞分裂’。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "child_name": {
                                "type": "string",
                                "description": "新 Agent 的名称 (例如 'frontend_worker')",
                            },
                            "objective": {
                                "type": "string",
                                "description": "子代 Agent 的具体目标",
                            },
                        },
                        "required": ["child_name", "objective"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "merge_child",
                    "description": "将完成任务的子代 Agent 合并回母体。吸收其知识和结果，并删除子文件。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "child_file": {
                                "type": "string",
                                "description": "子代 Agent 的文件名 (例如 'Genesis-Explorer.md')",
                            }
                        },
                        "required": ["child_file"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_folder",
                    "description": "创建文件夹。用于在文件系统中创建新目录。注意：此工具仅用于创建文件夹，不能用于创建文件。只有当任务涉及创建不带扩展名的目录路径时才使用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "要创建的文件夹路径，不应包含文件扩展名。例如：'task' 或 'src/components'",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "synthesize",
                    "description": "将两个agent的md文件内容合成一个新文件。保留第一个文件的Agent部分，合并其他部分内容。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_a": {
                                "type": "string",
                                "description": "第一个agent文件路径",
                            },
                            "file_b": {
                                "type": "string",
                                "description": "第二个agent文件路径",
                            },
                            "output_file": {
                                "type": "string",
                                "description": "合成后输出的文件路径",
                            }
                        },
                        "required": ["file_a", "file_b", "output_file"],
                    },
                },
            },
        ]

    def generate(self, agent, knowledge, memory, task, tools) -> Plan:
        print("\n--- [LLM 输入上下文] ---")
        print(f"任务: {task}")
        print("---------------------------\n")

        system_prompt = f"""你是 {agent.get('name', 'Genesis AI')}。
目标: {agent.get('objective', 'Evolve')}
风格: {agent.get('style', 'Concise')}

[核心法则]
1. **先看记忆 (Memory)**：不要重复失败的行动。如果上次尝试失败了，换一个方法。
2. 如果在记忆中看到类似任务，复用其结果。
3. **行动优先**：
   - 创建文件（带有扩展名如 login.html, index.js 等）→ 直接用 'write_file'
   - 创建文件夹（没有扩展名的路径）→ 用 'create_folder'
   - **修改文件** → 直接用 'write_file' 写入新内容（不要只读取不写入）
4. **关键区别**：
   - 文件路径必须包含扩展名（如 .html, .js, .txt），使用 write_file
   - 文件夹路径不含扩展名，使用 create_folder
   - 例如：'task/login.html' 是文件，使用 write_file；'task' 是文件夹，使用 create_folder
5. **错误处理**：
   - 如果文件不存在且任务是"创建"，直接用 'write_file' 创建，不要反复 'read_file'
   - 如果文件夹已存在，继续下一步，不要重复创建
6. **避免无效循环**：
   - 如果上次已经读取了文件内容，这次就应该写入修改后的内容
   - 不要连续多次只读取不写入
7. 仅当任务极其宏大且无法单次完成时，才使用 'add_task'。

你的当前状态:
[知识库]: {knowledge}
[记忆 (近期经验)]: {memory}
"""

        user_prompt = f"""当前任务: {task.content}
        
回顾你的记忆。你之前尝试过吗？什么有效？
**重要**：如果任务是"修改"文件，直接用 write_file 写入完整的新内容，不要只读取。
决定你的下一步行动（调用工具）或提供最终答案。
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
            "tools": self._get_tool_schemas(),
            "tool_choice": "auto",
        }

        try:
            print("[LLM] 正在向本地模型发送请求...")
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=600,
            )
            response.raise_for_status()
            result = response.json()

            choice = result["choices"][0]
            message = choice["message"]
            content = message.get("content", "") or ""

            # Check for tool calls
            if message.get("tool_calls"):
                tool_call_data = message["tool_calls"][0]
                function_name = tool_call_data["function"]["name"]
                arguments = json.loads(tool_call_data["function"]["arguments"])

                return Plan(
                    thought=f"我应该调用 {function_name}，参数为 {arguments}",
                    tool_call=ToolCall(name=function_name, args=arguments),
                )

            # Check for simple final answer or thought
            return Plan(
                thought=content, final_answer=content if "DONE" in content else None
            )

        except Exception as e:
            print(f"[LLM 错误] {e}")
            # Fallback for demonstration when local LLM is down
            if "Task Manager" in task.content:
                if "README" not in str(memory):
                    return Plan(
                        thought="本地大脑离线，但我知道必须分解这个任务。步骤 1: 设计。",
                        tool_call=ToolCall(
                            name="add_task",
                            args={"task": "Create README.md with architecture design"},
                        ),
                    )
                elif "index.html" not in str(memory):
                    return Plan(
                        thought="步骤 2: 前端结构。",
                        tool_call=ToolCall(
                            name="add_task",
                            args={"task": "Create index.html with basic layout"},
                        ),
                    )

            return Plan(
                thought="我调用大脑时遇到错误，且没有预设的应急方案。",
                final_answer="Error",
            )

    def distill_knowledge(self, memories: List[str]) -> List[str]:
        print("\n--- [正在蒸馏知识] ---")
        memory_text = "\n".join(memories)

        system_prompt = "你是知识档案馆管理员。你的目标是从临时的记忆日志中提取通用的真理、可复用的规则和关键洞察。"
        user_prompt = f"""分析以下记忆日志并提取关键洞察。
忽略具体的时间戳或琐碎细节。关注“什么有效”、“什么无效”以及“如何做”。
只返回洞察列表，每行一条简短的字符串。

[记忆日志]:
{memory_text}

[新洞察]:
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512,
        }

        try:
            # Send request (Using same fallback logic if needed or just try/except)
            # For brevity assuming main generator logic or simple request
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=600,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # Simple parsing: split by newlines
            insights = [
                line.strip("- *").strip()
                for line in content.split("\n")
                if line.strip()
            ]
            return insights

        except Exception as e:
            print(f"[蒸馏错误] {e}")
            return []

    def summarize_memory(
        self, task: str, thought: str, action: str, result: str
    ) -> str:
        """
        调用LLM生成精简的记忆摘要
        输入: 任务、思考、行动、结果
        输出: 一条精简的记忆(限100字)
        """
        system_prompt = "你是记忆总结专家。将操作记录总结为一条精简的记忆,限100字以内。"
        user_prompt = f"""请将以下操作总结为一条精简的记忆(限100字):

任务: {task}
思考: {thought}
行动: {action}
结果: {result[:200]}  # 结果可能很长,只取前200字

要求:
1. 只记录关键信息:任务目标、使用的工具、成功/失败
2. 忽略冗长的HTML/代码内容
3. 一句话概括,不超过100字
4. 格式: 任务 → 工具 → 结果

记忆摘要:
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 100,
        }

        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30,
            )
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"].strip()
            return summary[:100]  # 强制限制100字
        except Exception as e:
            # 如果LLM失败,返回简化版本
            return f"{task[:30]} → {action[:20]} → {'成功' if 'Error' not in str(result) else '失败'}"
