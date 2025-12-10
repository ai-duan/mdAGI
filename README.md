# Genesis Prime: AI Agent Runtime System

## Overview
Genesis Prime is an experimental AI agent runtime system designed to create, manage, and evolve autonomous AI agents. Built with Python, it enables agents to perceive their environment, plan actions, execute tasks, and learn from experiences.

## Core Concepts
- **Agent Creation**: Spawn specialized AI agents with dedicated objectives through mitosis
- **Task Management**: Handle complex tasks through decomposition and execution
- **Memory System**: Agents learn and retain knowledge through experiences
- **Self-Evolution**: Agents can merge back into the parent, sharing acquired knowledge

## Key Features
- Autonomous agent lifecycle management (creation, execution, merging)
- Persistent state storage in markdown format
- Memory distillation to convert experiences into actionable knowledge
- Command-line interface for agent interaction
- Support for various tools (file operations, agent creation, etc.)

## Project Structure
- `cli.py` - Command-line interface for interacting with agents
- `runtime/` - Core runtime engine
  - `runtime.py` - Main agent runtime logic
  - `state.py` - Agent state management
  - `parser.py` - Markdown file parsing and serialization
  - `llm.py` - Simplified LLM interface
  - `executor.py` - Tool execution engine
- `genesis_v1.md` - Initial agent DNA template

## Getting Started

1. Ensure you have Python 3.7+ installed
2. Clone the repository
3. Run the agent with the default DNA file:
   ```bash
   python cli.py
   ```
4. For continuous operation:
   ```bash
   python cli.py --forever
   ```
5. To run for a specific number of cycles:
   ```bash
   python cli.py --loop 5
   ```

## Usage Examples

### Basic Interaction
```bash
python cli.py
# Follow the prompts to add tasks
```

### Continuous Operation
```bash
python cli.py --forever
# Agent will continuously process tasks and wait for new ones
```

### Custom DNA File
```bash
python cli.py my_agent.md
# Run with a custom agent DNA file
```

## Agent Lifecycle

1. **Creation**: Agents are created from DNA templates in markdown format
2. **Perception**: Agents analyze their environment and pending tasks
3. **Planning**: Agents formulate plans using built-in reasoning
4. **Action**: Agents execute tools or create sub-agents
5. **Memory**: Actions and results are stored as experiences
6. **Distillation**: Excess memories are converted to permanent knowledge
7. **Merging**: Sub-agents can merge back, sharing knowledge with parents

## Available Tools

- `read_file` - Read file contents
- `write_file` - Write content to a file
- `add_task` - Add a new task to the queue
- `mitosis` - Create a specialized sub-agent
- `merge_child` - Merge a sub-agent back into the parent

## License
MIT