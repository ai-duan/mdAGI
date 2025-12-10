import re
from .state import AgentState, TodoItem


def parse_tag_content(text: str, tag: str) -> str:
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_agent(text: str) -> dict:
    content = parse_tag_content(text, "agent")
    data = {}
    for line in content.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()
    return data


def parse_list(text: str, tag: str) -> list:
    content = parse_tag_content(text, tag)
    # Simple line-based/dash-based definition for now
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    return lines


def parse_todo(text: str) -> list:
    content = parse_tag_content(text, "todo")
    todos = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        status = "PENDING"
        task_content = line

        # 1. Standard Markdown Checkboxes
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            is_done = "[x]" in line.lower()
            status = "DONE" if is_done else "PENDING"
            task_content = line.split("]", 1)[1].strip()

        # 2. Simplified Human Syntax (?, !, ？, ！)
        # Starts with ? or ？ -> PENDING
        elif line.startswith("? ") or line.startswith("？ "):
            status = "PENDING"
            task_content = line[1:].strip()

        # Starts with ! or ！ -> DONE
        elif line.startswith("! ") or line.startswith("！ "):
            status = "DONE"
            task_content = line[1:].strip()

        # 3. Legacy Bracket Syntax [PENDING]
        elif line.startswith("["):
            match = re.match(r"\[(.*?)\] (.*)", line)
            if match:
                status, task_content = match.groups()
                # Compat: Map old statuses
                if status == "PENDING":
                    status = "PENDING"
                if status == "DONE":
                    status = "DONE"

        # 4. Fallback (Plain text is pending)
        todos.append(TodoItem(content=task_content, status=status))

    return todos


def parse_md(text: str) -> AgentState:
    return AgentState(
        agent=parse_agent(text),
        knowledge=parse_list(text, "knowledge"),
        memory=parse_list(text, "memory"),
        code=parse_list(text, "code"),
        todo=parse_todo(text),
    )


def dump_state(state: AgentState) -> str:
    # Reconstruct the MD file - minimal implementation
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
        # Dump using the new simplified syntax
        if item.status == "DONE":
            md += f"! {item.content}\n"
        else:
            md += f"? {item.content}\n"
    md += "</todo>\n"

    return md
