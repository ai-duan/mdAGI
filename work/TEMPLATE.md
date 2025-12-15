# AML (Agent Markup Language) 模板

复制此文件并重命名为小写任务名，如 `1212-login-page.md`

---

<agent>
name: 任务名称
objective: 清晰描述要完成的目标
style: 行为风格（如：简洁高效、细致严谨）
</agent>

<knowledge>
[领域知识]
- 与任务相关的背景知识
- 技术约束或规范
[可用工具]
- read_file: 读取文件
- write_file: 写入文件
- create_folder: 创建文件夹
- add_task: 添加子任务
- mitosis: 创建子Agent
- merge_child: 融合子Agent
</knowledge>

<memory>
</memory>

<code>
# 相关代码片段或配置
</code>

<todo>
? 第一个待处理任务
? 第二个待处理任务
</todo>
