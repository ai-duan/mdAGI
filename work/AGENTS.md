# work/ 目录说明

## 用途

此目录存放 Genesis Agent 的任务文件（DNA 文件）。每个 `.md` 文件代表一个独立的 Agent 实例。

## 任务文件格式

```markdown
<agent>
name: Agent名称
objective: 目标描述
style: 行为风格
</agent>

<knowledge>
[公理/知识条目]
- 条目1
- 条目2
</knowledge>

<memory>
[时间戳] 记忆条目
</memory>

<code>
# 代码片段或运行时说明
</code>

<todo>
! 已完成任务
? 待处理任务
</todo>
```

## Todo 状态标记

| 标记 | 含义 |
|------|------|
| `?` | PENDING - 待处理 |
| `!` | DONE - 已完成 |

## 批量处理

使用以下命令处理此目录中的所有任务文件：

```bash
python cli.py --work
```

系统会遍历所有 `.md` 文件，为每个文件创建独立的 runtime 并执行待处理任务。

## 注意事项

- 每个文件是独立的 Agent，拥有自己的知识、记忆和任务
- 子 Agent（通过 mitosis 创建）也会生成在此目录或项目根目录
- 记忆超过 100 条时会自动蒸馏为知识
