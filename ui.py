#!/usr/bin/env python
"""
Standalone launcher for Genesis Agent Web UI.

Usage:
    python ui.py [--share]
"""
import argparse

from ui.app import launch_ui


def main():
    parser = argparse.ArgumentParser(
        description="Genesis Agent Web UI"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="生成公开分享链接"
    )
    args = parser.parse_args()
    
    print("🌐 启动 Genesis Agent Web UI...")
    launch_ui(share=args.share)


if __name__ == "__main__":
    main()
