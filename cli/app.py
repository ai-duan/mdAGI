"""Genesis Agent CLI 主应用"""
import argparse
from cli.commands import run_command, work_command, select_command, ui_command


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="genesis",
        description="Genesis Agent CLI - 双模式AGI系统"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行 DNA 文件")
    run_parser.add_argument("file", nargs="?", default="genesis_v1.md", help="DNA 文件路径")
    run_parser.add_argument("-l", "--loop", type=int, default=1, help="生命循环次数")
    run_parser.add_argument("-f", "--forever", action="store_true", help="持续运行直到停止")
    run_parser.add_argument(
        "-m", "--mode", 
        choices=["foreground", "background", "dual"], 
        default="foreground",
        help="运行模式"
    )

    # work 命令
    subparsers.add_parser("work", help="批量处理 work/ 目录中的任务")

    # ui 命令
    ui_parser = subparsers.add_parser("ui", help="启动 Gradio Web UI")
    ui_parser.add_argument(
        "--share",
        action="store_true",
        help="生成公开分享链接"
    )

    return parser


def main():
    """CLI 入口点"""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "run":
        run_command(
            file=args.file,
            mode=args.mode,
            loop=args.loop,
            forever=args.forever
        )
    elif args.command == "work":
        work_command()
    elif args.command == "ui":
        ui_command(share=args.share)
    else:
        # 无子命令时，显示任务选择菜单
        select_command()


if __name__ == "__main__":
    main()
