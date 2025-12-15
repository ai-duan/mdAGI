"""ui 命令 - 启动 Gradio Web UI"""


def ui_command(share: bool = False):
    """启动 Gradio Web UI"""
    from ui.app import launch_ui
    
    print("🌐 启动 Genesis Agent Web UI...")
    launch_ui(share=share)
