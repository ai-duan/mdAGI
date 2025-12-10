import argparse
import sys
from runtime.runtime import AgentRuntime


def main():
    parser = argparse.ArgumentParser(description="Genesis Agent CLI")
    parser.add_argument(
        "file", nargs="?", default="genesis_v1.md", help="Path to the Genesis DNA file"
    )
    parser.add_argument(
        "--loop", "-l", type=int, default=1, help="Number of life loops to run"
    )
    parser.add_argument(
        "--forever", "-f", action="store_true", help="Run forever until stopped"
    )

    args = parser.parse_args()

    print(f"🔥 在 {args.file} 上启动 Genesis 运行时...")
    try:
        runtime = AgentRuntime(args.file)
    except FileNotFoundError:
        print(f"错误: 找不到 DNA 文件 '{args.file}'。")
        sys.exit(1)

    # Interactive Mode: Ask for orders if not running just a loop
    if not args.forever and args.loop == 1:
        print("\n🤖 Genesis 正在聆听。新任务为何？(按回车键跳过)")
        user_input = input("> ").strip()
        if user_input:
            from runtime.state import TodoItem

            print(f"📝 添加任务: {user_input}")
            runtime.state.todo.insert(0, TodoItem(content=user_input, status="PENDING"))
            runtime.save()

    count = 0
    try:
        from runtime.state import TodoItem  # Lazy import for task creation

        while True:
            # Check exit condition for fixed loops
            if not args.forever and count >= args.loop:
                break

            # Reload state to see if there are pending tasks
            runtime.reload()
            current_task = runtime.state.next_pending_todo()

            if not current_task:
                # Idle state handling
                if args.forever:
                    print(
                        "\n💤 当前无待办任务。Genesis 正在聆听新任务... (输入新任务，直接回车退出)"
                    )
                    user_input = input("> ").strip()

                    if not user_input:
                        print("👋 用户选择退出。")
                        break

                    print(f"📝 添加任务: {user_input}")
                    runtime.state.todo.insert(
                        0, TodoItem(content=user_input, status="PENDING")
                    )
                    runtime.save()
                    # Continue gracefully to process the new task
                else:
                    # If not forever and no tasks, we just stop (or could prompt, but sticking to logic)
                    print("没有待办任务。结束运行。")
                    break

            # Execute run_once if there is a task (or we just added one)
            # Note: We reload again inside run_once, which is fine/safe.
            print(f"\n⚡ 轮回 {count+1}")
            runtime.run_once()
            count += 1

    except KeyboardInterrupt:
        print("\n🛑 生命循环被用户中断。")
    except Exception as e:
        print(f"\n💥 运行时严重故障: {e}")

    print("✨ Genesis 运行时已终止。")


if __name__ == "__main__":
    main()
