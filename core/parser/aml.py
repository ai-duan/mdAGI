"""AML (Agent Markup Language) 解析器"""
import re
from core.state.models import AgentState, TodoItem


def _parse_tag_content(text: str, tag: str) -> str:
    """提取标签内容"""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_agent(text: str) -> dict:
    """解析 <agent> 标签"""
    content = _parse_tag_content(text, "agent")
    data = {}
    for line in content.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()
    return data


def _parse_list(text: str, tag: str) -> list:
    """解析列表类标签"""
    content = _parse_tag_content(text, tag)
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    return lines


def _parse_todo(text: str) -> list:
    """解析 <todo> 标签"""
    content = _parse_tag_content(text, "todo")
    todos = []
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        status = "PENDING"
        task_content = line

        # Markdown Checkboxes: - [ ] / - [x]
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            is_done = "[x]" in line.lower()
            status = "DONE" if is_done else "PENDING"
            task_content = line.split("]", 1)[1].strip()

        # 简化语法: ? (待处理) / ! (已完成)
        elif line.startswith("? ") or line.startswith("？ "):
            status = "PENDING"
            task_content = line[1:].strip()
        elif line.startswith("! ") or line.startswith("！ "):
            status = "DONE"
            task_content = line[1:].strip()

        # 旧版语法: [PENDING] / [DONE]
        elif line.startswith("["):
            match = re.match(r"\[(.*?)\] (.*)", line)
            if match:
                status, task_content = match.groups()

        todos.append(TodoItem(content=task_content, status=status))

    return todos


def parse_aml(text: str) -> AgentState:
    """解析 AML 文本为 AgentState"""
    return AgentState(
        agent=_parse_agent(text),
        knowledge=_parse_list(text, "knowledge"),
        memory=_parse_list(text, "memory"),
        code=_parse_list(text, "code"),
        todo=_parse_todo(text),
    )


def dump_aml(state: AgentState) -> str:
    """将 AgentState 序列化为 AML 文本"""
    md = ""

    md += "<agent>\n"
    for k, v in state.agent.items():
        md += f"{k}: {v}\n"
    md += "</agent>\n\n"

    md += "<knowledge>\n"
    md += "\n".join(state.knowledge)
    md += "\n</knowledge>\n\n"

    md += "<memory>\n"
    md += "\n".join(state.memory)
    md += "\n</memory>\n\n"

    md += "<code>\n"
    md += "\n".join(state.code)
    md += "\n</code>\n\n"

    md += "<todo>\n"
    for item in state.todo:
        prefix = "!" if item.status == "DONE" else "?"
        md += f"{prefix} {item.content}\n"
    md += "</todo>\n"

    return md
