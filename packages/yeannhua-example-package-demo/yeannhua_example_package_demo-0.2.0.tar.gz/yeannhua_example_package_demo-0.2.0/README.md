# Example Package

一个简单的 Python 包示例，用于演示如何发布到 PyPI。

## 功能特性

- 简单的字符串处理函数
- 数值计算函数
- 字典格式化和打印工具

## 安装

```bash
pip install yeannhua-example-package-demo
```

## 使用方法

### 基本函数

```python
from example_package import hello, add

# 使用 hello 函数
print(hello("World"))
# 输出: Hello, World!

# 使用 add 函数
result = add(1, 2)
print(result)
# 输出: 3
```

### 字典打印工具

```python
from example_package import print_dict

# 格式化打印字典
data = {
    "name": "John",
    "age": 30,
    "hobbies": ["reading", "coding"],
    "address": {
        "city": "Shanghai",
        "country": "China"
    }
}

print_dict(data)
# 输出格式化的 JSON 字符串
```

## 运行示例

```bash
python -m example_package.main

# 或运行完整的测试示例
python3 examples/test.py
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 发布

```bash
# 发布到 TestPyPI（测试）
./scripts/publish_testpypi.sh

# 发布到正式 PyPI
./scripts/publish_pypi.sh
```

## 文档

- [更新日志](CHANGELOG.md) - 版本更新历史
- [发布指南](docs/release.md) - 如何发布新版本
- [上传说明](docs/upload_instructions.md) - 上传到 PyPI 的详细说明
- [项目结构](docs/project_structure.md) - 项目目录结构说明
- [文件命名规范](docs/naming_convention.md) - 文件命名规则
- [项目总结](docs/summary.md) - 项目完成情况总结

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本更新历史。

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件
