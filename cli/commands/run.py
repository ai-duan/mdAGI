"""run 命令 - 运行单个 DNA 文件"""
import sys
from core import Agent, TodoItem
from cli.utils import load_meta_prompt


def run_command(file: str, mode: str, loop: int, forever: bool):
    """执行 DNA 文件的生命循环
    
    Agent 会自动执行所有任务直到完成：
    - 每个任务最多执行 10 步
    - 每个任务最多重试 3 次
    - 失败的任务会记录原因并创建后续任务
    """
    
    # 后台模式特殊处理
    if mode == "background":
        file = ".ai/wake.md"
        meta_prompt = load_meta_prompt()
        if meta_prompt:
            print("📜 已加载 .ai/meta.md 作为系统提示词")
        print("🌙 后台模式：自我进化中...")
    elif mode == "dual":
        print("🔄 双模式：前台服务用户 + 后台自我进化")
    else:
        print("☀️ 前台模式：服务用户交互")

    print(f"🔥 在 {file} 上启动 Genesis 运行时...")
    
    try:
        agent = Agent(file, mode=mode)
    except FileNotFoundError:
        print(f"错误: 找不到 DNA 文件 '{file}'。")
        sys.exit(1)

    # 交互模式：询问初始任务
    if not forever:
        print("\n🤖 Genesis 正在聆听。新任务为何？(按回车键跳过)")
        user_input = input("> ").strip()
        if user_input:
            print(f"📝 添加任务: {user_input}")
            agent.state.todo.insert(0, TodoItem(content=user_input, status="PENDING"))
            agent.save()
            agent.note_interaction("user_add_task_initial")

    try:
        if forever:
            # 持续运行模式
            while True:
                agent.reload()
                
                # 执行所有当前任务
                stats = agent.run_all()
                
                if stats["total"] == 0:
                    print("\n💤 当前无待办任务。Genesis 正在聆听新任务... (输入新任务，直接回车退出)")
                    user_input = input("> ").strip()
                    if not user_input:
                        print("👋 用户选择退出。")
                        break
                    print(f"📝 添加任务: {user_input}")
                    agent.state.todo.insert(0, TodoItem(content=user_input, status="PENDING"))
                    agent.save()
                    agent.note_interaction("user_add_task_forever")
        else:
            # 单次运行模式：执行所有任务直到完成
            agent.run_all()

    except KeyboardInterrupt:
        print("\n🛑 生命循环被用户中断。")
    except Exception as e:
        print(f"\n💥 运行时严重故障: {e}")

    print("✨ Genesis 运行时已终止。")
    agent.stop()
