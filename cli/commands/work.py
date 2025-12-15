"""work 命令 - 批量处理 work/ 目录中的任务文件"""
from pathlib import Path
from core import Agent


def work_command():
    """处理 work/ 目录中的所有任务文件"""
    work_dir = Path("work")
    
    if not work_dir.exists():
        print("📁 work/ 目录不存在，创建中...")
        work_dir.mkdir()
        return

    # 过滤掉大写的元文件（AGENTS.md, TEMPLATE.md 等）
    md_files = [f for f in work_dir.glob("*.md") if f.name[0].islower()]
    
    if not md_files:
        print("📭 work/ 目录中没有任务文件")
        return

    print(f"📋 发现 {len(md_files)} 个任务文件")

    for md_file in md_files:
        print(f"\n--- 处理: {md_file} ---")
        try:
            agent = Agent(str(md_file), start_background=False, mode="foreground")
            pending = agent.state.next_pending_todo()
            
            if pending:
                print(f"⚡ 执行任务: {pending.content}")
                agent.run_once()
            else:
                print(f"✅ 无待完成任务")
        except Exception as e:
            print(f"❌ 处理失败: {e}")

    print("\n📦 work/ 目录任务处理完成")
