#!/usr/bin/env python3
"""
MCP服务器stdio启动脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    try:
        from server import server
        print("服务器导入成功，开始stdio模式...", file=sys.stderr)
        # 直接调用server的run_stdio_async方法，避免anyio.run
        import asyncio
        asyncio.run(server.run_stdio_async())
    except Exception as e:
        print(f"启动服务器失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()