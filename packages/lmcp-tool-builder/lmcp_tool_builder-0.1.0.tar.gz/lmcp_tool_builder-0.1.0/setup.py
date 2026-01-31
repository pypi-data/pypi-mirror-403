#!/usr/bin/env python3
"""
LMCP Tool Builder - PyPI 包配置
"""

from setuptools import setup, find_packages
import os

# 读取 README.md 作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lmcp-tool-builder",
    version="0.1.0",
    author="LMCP Team",
    author_email="support@lmcp.dev",
    description="LMCP Tool Builder - 简化 LangChain 工具加载和集成",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lmcp-dev/lmcp-tool-builder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "twine>=4.0.0",
            "build>=0.10.0",
        ],
        "langchain": [
            "langchain>=0.1.0",
            "langchain-openai>=0.0.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "lmcp-tool-builder=lmcp_tool_builder.cli:main",
        ],
    },
    include_package_data=True,
    keywords=[
        "lmcp",
        "langchain",
        "tools",
        "ai",
        "llm",
        "agent",
        "tool-builder",
        "tool-management",
    ],
    project_urls={
        "Bug Reports": "https://github.com/lmcp-dev/lmcp-tool-builder/issues",
        "Source": "https://github.com/lmcp-dev/lmcp-tool-builder",
        "Documentation": "https://lmcp.dev/docs/tool-builder",
    },
)
