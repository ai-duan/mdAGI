# AGENTS.md

## 项目概述

Genesis Agent 是一个基于 Markdown 的自主 AGI 系统，支持双模式运行（前台交互/后台自我进化）。系统通过解析 AML (Agent Markup Language) 文件作为"DNA"来驱动 Agent 的行为。

## 核心架构

```
cli.py                  # CLI 入口
cli/
├── app.py              # 主应用 + 参数解析
├── commands/
│   ├── run.py          # run 命令
│   └── work.py         # work 命令
└── utils/
    └── config.py       # 配置加载

core/                   # AGI 运行时内核
├── agent.py            # Agent 主类（对外统一接口）
├── loop.py             # 生命循环（感知→规划→行动→记忆→沉淀）
├── state/              # 状态管理
│   ├── models.py       # 数据模型（AgentState, TodoItem）
│   └── store.py        # 状态持久化
├── mind/               # 认知层
│   ├── llm.py          # LLM 客户端
│   ├── planner.py      # 规划器
│   └── memory.py       # 记忆管理 + 知识蒸馏
├── tools/              # 工具层
│   ├── registry.py     # 工具注册表
│   ├── executor.py     # 工具执行器
│   └── builtins.py     # 内置工具
├── parser/             # AML 解析
│   └── aml.py          # AML 解析器
└── scheduler/          # 调度层
    └── background.py   # 后台监控 + 自省
```

## 运行模式

- `foreground`: 前台模式，服务用户交互
- `background`: 后台模式，自我进化（加载 `.ai/meta.md`）
- `dual`: 双模式

## 使用示例

```bash
python cli.py run genesis_v1.md      # 运行 DNA 文件
python cli.py run -m background -f   # 后台持续运行
python cli.py work                   # 批量处理 work/
```

## 特殊目录

- `.ai/meta.md`: 系统级提示词
- `.ai/wake.md`: 自省任务文件
- `work/`: 任务文件目录

## 配置常量

- `MEMORY_LIMIT = 100`: 记忆库容量上限
- `KEEP_COUNT = 3`: 蒸馏后保留的记忆条数
- `IDLE_TIMEOUT_SECONDS = 30`: 空闲检测超时
