# 示例代码

本目录包含 `example_package` 的使用示例。

## 前置要求

运行示例前，需要先安装包：

```bash
# 方式一：开发模式安装（推荐）
cd /Users/admin/Downloads/sdk-generation/pypi/example_package
pip install -e .

# 方式二：正常安装
pip install yeannhua-example-package-demo
```

## 示例文件

### test.py
完整的功能测试示例，展示所有可用功能：
- `hello()` - 字符串问候函数
- `add()` - 数值计算函数
- `print_dict()` - 字典格式化打印函数（v0.2.0 新增）

## 运行示例

```bash
# 在 example_package 目录内运行
cd /Users/admin/Downloads/sdk-generation/pypi/example_package
python3 examples/test.py
```

**预期输出**：
```
==================================================
测试 example_package v0.2.0
==================================================

1. 测试 hello 函数
------------------------------
Hello, World!
Hello, Python开发者!

2. 测试 add 函数
------------------------------
1 + 2 = 3
100 + 200 = 300

3. 测试 print_dict 函数
------------------------------
...（格式化的 JSON 输出）
```

## 快速测试命令

```bash
# 测试单个函数
python3 -c "from example_package import hello; print(hello('测试'))"
python3 -c "from example_package import add; print(add(5, 10))"
python3 -c "from example_package import print_dict; print_dict({'test': 'ok'})"
```

## 添加你自己的示例

欢迎添加更多示例文件到此目录！示例文件命名建议使用小写字母和下划线，如：
- `basic_usage.py`
- `advanced_features.py`
- `custom_example.py`
