"""
Gradio Web UI for Genesis Agent.

Provides a web-based interface for running and managing Agents.
"""

import os
import gradio as gr

from ui.service import AgentUIService, AgentStateView


# Status indicator styles
STATUS_RUNNING = "🟢 运行中"
STATUS_STOPPED = "⚪ 已停止"
STATUS_ERROR = "🔴 错误"
STATUS_SUCCESS = "✅ 成功"


def create_ui() -> gr.Blocks:
    """Create and configure the Gradio UI."""
    service = AgentUIService()
    
    def get_dna_files() -> list[str]:
        """Get list of available DNA files."""
        files = []
        # Check work directory
        if os.path.isdir("work"):
            for f in os.listdir("work"):
                if f.endswith(".md") and f == f.lower():
                    files.append(os.path.join("work", f))
        # Check root directory for .md files
        for f in os.listdir("."):
            if f.endswith(".md") and os.path.isfile(f):
                files.append(f)
        return files
    
    def refresh_file_list():
        """Refresh the DNA file dropdown."""
        return gr.update(choices=get_dna_files())
    
    def refresh_task_list():
        """Refresh the task file list."""
        task_files = service.list_task_files()
        data = [[tf.path, tf.name, tf.pending_count] for tf in task_files]
        return data
    
    def run_agent_with_status(file: str, mode: str):
        """Run agent and yield status updates with logs."""
        # Initial status: running
        yield STATUS_RUNNING, ""
        
        logs = []
        try:
            for log_line in service.run_agent(file, mode):
                logs.append(log_line)
                full_log = "\n".join(logs)
                # Check if error occurred
                if log_line.startswith("❌"):
                    yield STATUS_ERROR, full_log
                else:
                    yield STATUS_RUNNING, full_log
            
            # Final status based on last log
            full_log = "\n".join(logs)
            if any(line.startswith("❌") for line in logs):
                yield STATUS_ERROR, full_log
            elif any(line.startswith("✅") for line in logs):
                yield STATUS_SUCCESS, full_log
            else:
                yield STATUS_STOPPED, full_log
        except Exception as e:
            logs.append(f"❌ 错误: {type(e).__name__}: {e}")
            yield STATUS_ERROR, "\n".join(logs)
    
    def stop_agent_with_notification():
        """Stop agent and return notification."""
        result = service.stop_agent()
        if result.startswith("⏹️"):
            return result, STATUS_STOPPED
        return result, STATUS_ERROR if result.startswith("❌") else STATUS_STOPPED
    
    def add_task_with_notification(task: str, file: str):
        """Add task and return notification."""
        result = service.add_task(task, file)
        notification_type = "success" if result.startswith("✅") else "error"
        return result, notification_type
    
    def batch_process_with_status():
        """Batch process and yield status updates."""
        yield STATUS_RUNNING, ""
        
        logs = []
        has_error = False
        for log_line in service.batch_process():
            logs.append(log_line)
            if log_line.strip().startswith("❌"):
                has_error = True
            yield STATUS_RUNNING, "\n".join(logs)
        
        full_log = "\n".join(logs)
        if has_error:
            yield STATUS_ERROR, full_log
        else:
            yield STATUS_SUCCESS, full_log
    
    def load_agent_state(file: str):
        """Load and display agent state."""
        if not file:
            return {}, "", "⚠️ 请选择一个文件"
        
        result = service.get_agent_state(file)
        if isinstance(result, str):
            # Error message
            return {}, "", result
        
        # Success - format state for display
        state_dict = {
            "agent_name": result.agent_name,
            "is_running": result.is_running,
            "todo_list": result.todo_list,
        }
        memory_text = "\n".join(result.memory) if result.memory else "(无记忆)"
        status = STATUS_RUNNING if result.is_running else STATUS_STOPPED
        return state_dict, memory_text, status
    
    with gr.Blocks(title="Genesis Agent") as app:
        gr.Markdown("# 🧬 Genesis Agent")
        
        # Tab 1: Run Agent
        with gr.Tab("运行 Agent"):
            with gr.Row():
                with gr.Column(scale=3):
                    file_input = gr.Dropdown(
                        label="DNA 文件", 
                        choices=get_dna_files(),
                        allow_custom_value=True
                    )
                with gr.Column(scale=1):
                    refresh_files_btn = gr.Button("🔄 刷新", size="sm")
            
            mode_input = gr.Radio(
                ["foreground", "background", "dual"],
                label="运行模式",
                value="foreground"
            )
            # 移除循环次数设置，Agent 会自动执行所有任务
            
            # Status indicator
            with gr.Row():
                status_indicator = gr.Textbox(
                    label="状态",
                    value=STATUS_STOPPED,
                    interactive=False,
                    scale=1
                )
            
            with gr.Row():
                run_btn = gr.Button("▶️ 运行", variant="primary")
                stop_btn = gr.Button("⏹️ 停止", variant="stop")
            
            output_log = gr.Textbox(
                label="输出日志", 
                lines=15, 
                interactive=False
            )
            
            # Notification area for run tab
            run_notification = gr.Textbox(
                label="通知",
                interactive=False,
                visible=True,
                max_lines=2
            )
        
        # Tab 2: Task Management
        with gr.Tab("任务管理"):
            # Status indicator for task management
            task_status = gr.Textbox(
                label="状态",
                value=STATUS_STOPPED,
                interactive=False
            )
            
            task_list = gr.Dataframe(
                label="任务文件",
                headers=["文件路径", "Agent 名称", "待办数量"],
                interactive=False,
                value=refresh_task_list()
            )
            refresh_btn = gr.Button("🔄 刷新列表")
            
            gr.Markdown("### 添加新任务")
            with gr.Row():
                task_file_select = gr.Dropdown(
                    label="目标文件",
                    choices=get_dna_files(),
                    allow_custom_value=True,
                    scale=2
                )
                new_task_input = gr.Textbox(
                    label="新任务", 
                    placeholder="输入任务描述...",
                    scale=3
                )
            add_task_btn = gr.Button("➕ 添加任务")
            task_notification = gr.Textbox(
                label="操作结果",
                interactive=False,
                max_lines=2
            )
            
            gr.Markdown("### 批量处理")
            batch_btn = gr.Button("🚀 批量处理所有任务", variant="primary")
            batch_output = gr.Textbox(
                label="处理进度", 
                lines=10, 
                interactive=False
            )
        
        # Tab 3: State View
        with gr.Tab("状态查看"):
            with gr.Row():
                state_file_select = gr.Dropdown(
                    label="选择 DNA 文件",
                    choices=get_dna_files(),
                    allow_custom_value=True,
                    scale=3
                )
                load_state_btn = gr.Button("📖 加载状态", scale=1)
            
            state_status = gr.Textbox(
                label="状态",
                value=STATUS_STOPPED,
                interactive=False
            )
            
            state_display = gr.JSON(label="Agent 状态")
            memory_display = gr.Textbox(
                label="记忆", 
                lines=10, 
                interactive=False
            )
        
        # Event handlers
        refresh_files_btn.click(
            fn=refresh_file_list,
            outputs=[file_input]
        )
        
        run_btn.click(
            fn=run_agent_with_status,
            inputs=[file_input, mode_input],
            outputs=[status_indicator, output_log]
        )
        
        stop_btn.click(
            fn=stop_agent_with_notification,
            outputs=[run_notification, status_indicator]
        )
        
        refresh_btn.click(
            fn=refresh_task_list,
            outputs=[task_list]
        )
        
        add_task_btn.click(
            fn=lambda task, file: service.add_task(task, file),
            inputs=[new_task_input, task_file_select],
            outputs=[task_notification]
        ).then(
            fn=refresh_task_list,
            outputs=[task_list]
        )
        
        batch_btn.click(
            fn=batch_process_with_status,
            outputs=[task_status, batch_output]
        ).then(
            fn=refresh_task_list,
            outputs=[task_list]
        )
        
        load_state_btn.click(
            fn=load_agent_state,
            inputs=[state_file_select],
            outputs=[state_display, memory_display, state_status]
        )
        
        # Auto-load state when file is selected
        state_file_select.change(
            fn=load_agent_state,
            inputs=[state_file_select],
            outputs=[state_display, memory_display, state_status]
        )
    
    return app


def launch_ui(share: bool = False) -> None:
    """Launch the Gradio UI."""
    app = create_ui()
    app.launch(share=share)


if __name__ == "__main__":
    launch_ui()
