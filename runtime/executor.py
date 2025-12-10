from .llm import ToolCall
import os


def read_file(path):
    print(f"[Executor] Reading {path}...")
    if not os.path.exists(path):
        return "Error: File not found."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    print(f"[Executor] Writing to {path}...")
    # 确保父目录存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "File written successfully."


def create_folder(path):
    print(f"[Executor] Creating folder {path}...")
    if os.path.exists(path):
        return f"Folder already exists: {path}"
    os.makedirs(path)
    return f"Folder created successfully: {path}"

def synthesize(file_a, file_b, output_file):
    print(f"[Executor] Synthesizing {file_a} and {file_b} into {output_file}...")
    
    # Check if both files exist
    if not os.path.exists(file_a):
        return f"Error: File A '{file_a}' not found."
    if not os.path.exists(file_b):
        return f"Error: File B '{file_b}' not found."
    
    # Read both files
    with open(file_a, "r", encoding="utf-8") as f:
        content_a = f.read()
    with open(file_b, "r", encoding="utf-8") as f:
        content_b = f.read()
    
    # Parse both files to extract sections
    from .parser import parse_md, dump_state
    state_a = parse_md(content_a)
    state_b = parse_md(content_b)
    
    # Create a new state with Agent from A and merged content
    synthesized_state = state_a
    
    # Merge knowledge (unique items from both)
    for k in state_b.knowledge:
        if k not in synthesized_state.knowledge:
            synthesized_state.knowledge.append(k)
    
    # Merge memory (all items from both)
    synthesized_state.memory.extend(state_b.memory)
    
    # Merge code (unique items from both)
    for c in state_b.code:
        if c not in synthesized_state.code:
            synthesized_state.code.append(c)
    
    # Merge todo (all items from both)
    synthesized_state.todo.extend(state_b.todo)
    
    # Dump the synthesized state to string
    synthesized_content = dump_state(synthesized_state)
    
    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(synthesized_content)
    
    return f"Synthesis successful. Output written to {output_file}"


BUILTIN_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "create_folder": create_folder,
    "synthesize": synthesize,
}


def execute_tool(call: ToolCall):
    if call.name in BUILTIN_TOOLS:
        try:
            result = BUILTIN_TOOLS[call.name](**call.args)
            return result
        except Exception as e:
            return f"Error executing tool: {e}"
    else:
        return f"Unknown tool: {call.name}"
