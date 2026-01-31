#!/usr/bin/env python3
"""
LMCP Tool Builder 命令行工具
"""

import argparse
import sys
from typing import List, Optional
from .builder import LMCPToolBuilder


def build_command(args):
    """构建工具命令"""
    print("🚀 LMCP Tool Builder - 构建工具")
    print("=" * 50)
    
    builder = LMCPToolBuilder(
        server_url=args.server_url,
        api_key=args.api_key,
        local_tools_file=args.local_tools_file,
        debug=args.debug
    )
    
    tools = builder.build_and_load_tools()
    
    if tools:
        print(f"\n✅ 成功构建并加载了 {len(tools)} 个工具")
        print("\n📋 工具列表:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.__name__}")
    else:
        print("\n❌ 没有找到可用的工具")
        sys.exit(1)


def test_command(args):
    """测试工具命令"""
    print("🧪 LMCP Tool Builder - 测试工具")
    print("=" * 50)
    
    builder = LMCPToolBuilder(
        server_url=args.server_url,
        api_key=args.api_key,
        local_tools_file=args.local_tools_file,
        debug=args.debug
    )
    
    # 加载工具
    tools = builder.load_tools_from_module()
    
    if not tools:
        print("❌ 没有找到可测试的工具")
        sys.exit(1)
    
    # 测试工具
    builder.test_tools(tools)


def discover_command(args):
    """发现工具命令"""
    print("🔍 LMCP Tool Builder - 发现工具")
    print("=" * 50)
    
    builder = LMCPToolBuilder(
        server_url=args.server_url,
        api_key=args.api_key,
        local_tools_file=args.local_tools_file,
        debug=args.debug
    )
    
    tools = builder.discover_tools()
    
    if tools:
        print(f"\n✅ 发现了 {len(tools)} 个工具")
        print("\n📋 工具预览:")
        for i, tool_code in enumerate(tools[:5], 1):  # 只显示前5个
            func_name = builder._extract_function_name(tool_code)
            print(f"  {i}. {func_name}")
            print(f"     代码预览: {tool_code[:100]}...")
        
        if len(tools) > 5:
            print(f"  ... 还有 {len(tools) - 5} 个工具未显示")
    else:
        print("\n❌ 没有发现工具")


def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        description="LMCP Tool Builder - 简化 LangChain 工具加载和集成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s build --server-url http://localhost:8000 --api-key your-key
  %(prog)s test --tools-file bot_tools.py
  %(prog)s discover --server-url http://localhost:8000 --api-key your-key --debug
        """
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # build 命令
    build_parser = subparsers.add_parser("build", help="构建并加载工具")
    build_parser.add_argument("--server-url", default="http://localhost:8000", 
                             help="LMCP服务器地址 (默认: http://localhost:8000)")
    build_parser.add_argument("--api-key", required=True, help="API密钥")
    build_parser.add_argument("--local-tools-file", default="bot_tools.py",
                             help="本地工具文件路径 (默认: bot_tools.py)")
    build_parser.add_argument("--debug", action="store_true", help="启用调试输出")
    build_parser.set_defaults(func=build_command)
    
    # test 命令
    test_parser = subparsers.add_parser("test", help="测试工具")
    test_parser.add_argument("--server-url", default="http://localhost:8000",
                            help="LMCP服务器地址 (默认: http://localhost:8000)")
    test_parser.add_argument("--api-key", help="API密钥")
    test_parser.add_argument("--local-tools-file", default="bot_tools.py",
                            help="本地工具文件路径 (默认: bot_tools.py)")
    test_parser.add_argument("--debug", action="store_true", help="启用调试输出")
    test_parser.set_defaults(func=test_command)
    
    # discover 命令
    discover_parser = subparsers.add_parser("discover", help="发现工具")
    discover_parser.add_argument("--server-url", default="http://localhost:8000",
                                help="LMCP服务器地址 (默认: http://localhost:8000)")
    discover_parser.add_argument("--api-key", required=True, help="API密钥")
    discover_parser.add_argument("--local-tools-file", default="bot_tools.py",
                                help="本地工具文件路径 (默认: bot_tools.py)")
    discover_parser.add_argument("--debug", action="store_true", help="启用调试输出")
    discover_parser.set_defaults(func=discover_command)
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ 错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
