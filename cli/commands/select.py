"""select 命令 - 交互式选择任务文件"""
from pathlib import Path
from core import Agent
from core.parser import parse_aml


def get_task_files() -> list[tuple[Path, str]]:
    """获取所有任务文件及其 Agent 名称"""
    work_dir = Path("work")
    
    if not work_dir.exists():
        return []
    
    # 过滤掉大写的元文件
    md_files = [f for f in work_dir.glob("*.md") if f.name[0].islower()]
    
    tasks = []
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            state = parse_aml(content)
            name = state.agent.get("name", md_file.stem)
            pending_count = sum(1 for t in state.todo if t.status == "PENDING")
            tasks.append((md_file, name, pending_count))
        except Exception:
            tasks.append((md_file, md_file.stem, 0))
    
    return tasks


def select_command():
    """交互式选择并运行任务文件"""
    tasks = get_task_files()
    
    if not tasks:
        print("📭 work/ 目录中没有任务文件")
        print("💡 提示: 复制 work/TEMPLATE.md 创建新任务")
        return
    
    # 显示菜单
    print("\n🚀 Genesis Agent - 选择任务\n")
    print("-" * 50)
    
    for i, (path, name, pending) in enumerate(tasks, 1):
        status = f"({pending} 待办)" if pending > 0 else "(✅ 已完成)"
        print(f"  [{i}] {name} {status}")
        print(f"      📄 {path}")
    
    print("-" * 50)
    print("  [0] 退出")
    print()
    
    # 获取用户选择
    try:
        choice = input("请选择 > ").strip()
        
        if not choice or choice == "0":
            print("👋 再见")
            return
        
        idx = int(choice) - 1
        if 0 <= idx < len(tasks):
            selected_file, name, _ = tasks[idx]
            print(f"\n🔥 启动: {name}")
            
            agent = Agent(str(selected_file), mode="foreground")
            
            # 运行循环
            while True:
                agent.reload()
                task = agent.state.next_pending_todo()
                
                if not task:
                    print("\n✅ 所有任务已完成")
                    print("输入新任务继续，或直接回车退出:")
                    user_input = input("> ").strip()
                    if not user_input:
                        break
                    from core.state import TodoItem
                    agent.state.todo.append(TodoItem(content=user_input, status="PENDING"))
                    agent.save()
                    continue
                
                agent.run_once()
            
            agent.stop()
        else:
            print("❌ 无效选择")
            
    except ValueError:
        print("❌ 请输入数字")
    except KeyboardInterrupt:
        print("\n🛑 已中断")
