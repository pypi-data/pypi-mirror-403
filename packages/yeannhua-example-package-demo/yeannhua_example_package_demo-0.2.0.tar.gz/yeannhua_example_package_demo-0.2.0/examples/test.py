#!/usr/bin/env python3
"""
example_package 使用示例（简单版本）

展示如何使用 example_package 中的各种功能
"""

import sys
import os

from example_package import hello, add, print_dict, __version__

print("=" * 50)
print(f"测试 example_package v{__version__}")
print("=" * 50)
print()

# 测试 hello 函数
print("1. 测试 hello 函数")
print("-" * 30)
print(hello("World"))
print(hello("Python开发者"))
print()

# 测试 add 函数
print("2. 测试 add 函数")
print("-" * 30)
result = add(1, 2)
print(f"1 + 2 = {result}")
print(f"100 + 200 = {add(100, 200)}")
print()

# 测试 print_dict 函数（新功能）
print("3. 测试 print_dict 函数")
print("-" * 30)

# 简单字典
simple_data = {"name": "测试", "value": 123}
print("简单字典:")
print_dict(simple_data)
print()

# 嵌套字典
nested_data = {
    "project": "example_package",
    "version": "0.2.0",
    "features": [
        "hello",
        "add",
        "print_dict"
    ],
    "metadata": {
        "author": "Example Author",
        "date": "2026-01-24"
    }
}
print("嵌套字典:")
print_dict(nested_data)
print()

# 包含列表的字典
list_data = {
    "users": [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ],
    "tags": ["python", "pypi", "demo"]
}
print("包含列表的字典:")
print_dict(list_data)
print()

print("=" * 50)
print("所有测试完成！")
print("=" * 50)
print()
print("提示：如需使用日志分级功能，请参考 examples/test_logging.py")
