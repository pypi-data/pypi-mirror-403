#!/usr/bin/env python3
"""
LMCP 工具构建器
封装工具发现、构建和加载功能
"""

import os
import ast
import inspect
import requests
from typing import List, Dict, Any, Optional
import importlib.util


class LMCPToolBuilder:
    """LMCP 工具构建器类"""
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 api_key: str = "",
                 local_tools_file: str = "bot_tools.py",
                 debug: bool = False):
        """
        初始化工具构建器
        
        Args:
            server_url: LMCP服务器地址
            api_key: API密钥
            local_tools_file: 本地工具文件路径
            debug: 是否输出调试信息
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.local_tools_file = local_tools_file
        self.debug = debug
    
    def _print_debug(self, message: str):
        """打印调试信息（仅在debug=True时输出）"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def _print_info(self, message: str):
        """打印信息（始终输出）"""
        print(f"[INFO] {message}")
    
    def discover_tools(self) -> List[str]:
        """
        从LMCP服务器发现工具
        如果服务器不可用或没有工具，则回退到本地工具
        
        Returns:
            List[str]: 工具代码列表
        """
        self._print_info(f"从服务器发现工具...")
        
        try:
            response = requests.get(
                f"{self.server_url}/api/tools/discover",
                headers={"X-API-Key": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tools = data.get("tools", [])
                    self._print_info(f"发现 {len(tools)} 个工具")
                    return tools
                else:
                    self._print_info(f"发现失败: {data.get('error')}")
            else:
                self._print_info(f"HTTP错误: {response.status_code}")
                
        except Exception as e:
            self._print_info(f"连接失败: {e}")
        
        # 服务器不可用，回退到本地工具
        self._print_info("服务器不可用，尝试使用本地工具")
        if os.path.exists(self.local_tools_file):
            self._print_info(f"使用本地工具文件: {self.local_tools_file}")
            try:
                with open(self.local_tools_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取所有函数代码
                local_tools = []
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_code = ast.unparse(node)
                        local_tools.append(func_code)
                
                self._print_info(f"加载 {len(local_tools)} 个本地工具")
                return local_tools
                
            except Exception as e:
                self._print_info(f"加载本地工具失败: {e}")
        else:
            self._print_info(f"本地工具文件不存在: {self.local_tools_file}")
        
        return []
    
    def _extract_function_name(self, code: str) -> str:
        """从代码中提取函数名"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except:
            pass
        return ""
    
    def _extract_function_code(self, code: str) -> str:
        """从代码中提取完整的函数定义"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return ast.unparse(node)
        except:
            pass
        return code
    
    def _compare_functions(self, func1: str, func2: str) -> bool:
        """比较两个函数是否相同"""
        name1 = self._extract_function_name(func1)
        name2 = self._extract_function_name(func2)
        
        if name1 != name2:
            return False
        
        code1 = self._extract_function_code(func1)
        code2 = self._extract_function_code(func2)
        
        return code1.strip() == code2.strip()
    
    def _load_local_tools(self) -> Dict[str, str]:
        """加载本地工具文件中的函数"""
        local_tools = {}
        
        if not os.path.exists(self.local_tools_file):
            self._print_debug(f"{self.local_tools_file} 不存在")
            return local_tools
        
        try:
            with open(self.local_tools_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析所有函数
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    func_code = ast.unparse(node)
                    local_tools[func_name] = func_code
            
            self._print_debug(f"加载 {len(local_tools)} 个本地工具")
            
        except Exception as e:
            self._print_debug(f"加载本地工具失败: {e}")
        
        return local_tools
    
    def build_tools_module(self, server_tools: List[str]) -> str:
        """构建工具模块"""
        self._print_info(f"构建工具模块...")
        
        # 加载本地工具
        local_tools = self._load_local_tools()
        
        # 分析服务器工具
        server_tool_dict = {}
        for tool_code in server_tools:
            func_name = self._extract_function_name(tool_code)
            if func_name:
                server_tool_dict[func_name] = tool_code
        
        # 合并工具（服务器优先）
        merged_tools = {}
        updated_count = 0
        new_count = 0
        
        # 首先添加所有服务器工具
        for func_name, tool_code in server_tool_dict.items():
            if func_name in local_tools:
                # 比较内容
                if self._compare_functions(tool_code, local_tools[func_name]):
                    # 内容相同，使用本地版本
                    merged_tools[func_name] = local_tools[func_name]
                else:
                    # 内容不同，使用服务器版本
                    merged_tools[func_name] = tool_code
                    updated_count += 1
                    self._print_debug(f"更新工具: {func_name}")
            else:
                # 新工具
                merged_tools[func_name] = tool_code
                new_count += 1
                self._print_debug(f"新增工具: {func_name}")
        
        # 添加本地独有的工具
        for func_name, tool_code in local_tools.items():
            if func_name not in merged_tools:
                merged_tools[func_name] = tool_code
        
        # 生成模块代码
        module_code = '''"""
自动生成的工具模块
包含从LMCP服务器同步的工具
"""

'''
        
        # 按函数名排序
        for func_name in sorted(merged_tools.keys()):
            module_code += f"\n{merged_tools[func_name]}\n"
        
        self._print_info(f"构建完成: {len(merged_tools)} 个工具")
        if updated_count > 0:
            self._print_debug(f"更新: {updated_count} 个")
        if new_count > 0:
            self._print_debug(f"新增: {new_count} 个")
        
        return module_code
    
    def save_tools_module(self, module_code: str):
        """保存工具模块到文件"""
        try:
            with open(self.local_tools_file, 'w', encoding='utf-8') as f:
                f.write(module_code)
            self._print_info(f"已保存到 {self.local_tools_file}")
        except Exception as e:
            self._print_info(f"保存失败: {e}")
    
    def load_tools_from_module(self) -> List:
        """从模块中加载工具函数"""
        tools = []
        
        if not os.path.exists(self.local_tools_file):
            self._print_info(f"{self.local_tools_file} 不存在")
            return tools
        
        try:
            # 动态导入
            spec = importlib.util.spec_from_file_location("bot_tools", self.local_tools_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取所有函数
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    tools.append(obj)
                    self._print_debug(f"加载: {name}")
            
            self._print_info(f"加载 {len(tools)} 个工具函数")
            
        except Exception as e:
            self._print_info(f"加载工具函数失败: {e}")
        
        return tools
    
    def build_and_load_tools(self) -> List:
        """
        构建并加载工具
        主要流程：
        1. 发现工具（已集成本地回退）
        2. 如果是服务器工具，构建并保存模块
        3. 加载工具函数
        
        Returns:
            List: 工具函数列表
        """
        self._print_info("=" * 50)
        self._print_info("LMCP 工具构建")
        self._print_info("=" * 50)
        
        # 1. 发现工具（已集成本地回退）
        tools_list = self.discover_tools()
        
        if not tools_list:
            self._print_info("无可用工具")
            return []
        
        # 2. 如果是服务器工具，构建并保存模块
        # 检查是否来自服务器（通过检查是否有完整的函数代码）
        is_from_server = any('def ' in tool for tool in tools_list)
        
        if is_from_server:
            # 构建工具模块
            module_code = self.build_tools_module(tools_list)
            
            # 保存模块
            self.save_tools_module(module_code)
        
        # 3. 加载工具函数
        tools = self.load_tools_from_module()
        
        return tools
    
    def test_tools(self, tools: List):
        """测试工具函数"""
        if not tools:
            self._print_info("没有可测试的工具")
            return
        
        self._print_info("\n测试工具函数:")
        
        for tool in tools:
            func_name = tool.__name__
            self._print_info(f"\n  {func_name}")
            
            # 获取参数
            sig = inspect.signature(tool)
            params = list(sig.parameters.keys())
            
            # 准备测试参数
            test_args = {}
            if "city" in params:
                test_args["city"] = "北京"
            if "query" in params:
                test_args["query"] = "测试"
            if "text" in params:
                test_args["text"] = "测试文本"
            if "a" in params and "b" in params:
                test_args["a"] = 10
                test_args["b"] = 20
            if "expression" in params:
                test_args["expression"] = "2 + 3"
            
            try:
                if test_args:
                    result = tool(**test_args)
                else:
                    result = tool()
                self._print_info(f"     结果: {result}")
            except Exception as e:
                self._print_info(f"     错误: {e}")
