# 文档目录

本目录包含项目的所有文档。

## 文档列表

### [CHANGELOG.md](../CHANGELOG.md)
**版本更新日志**（根目录）

记录每个版本的变更内容，包括：
- 新增功能
- 改进内容
- 修复的问题
- 破坏性变更

每次发布新版本时都应更新此文件。

### [release.md](01_release.md)
**发布指南**

详细说明如何发布新版本的步骤。

### [upload_instructions.md](01_upload_instructions.md)
**上传说明**

快速参考文档，说明如何上传到 PyPI。

### [project_structure.md](01_project_structure.md)
**项目结构说明**

详细说明项目的目录结构和文件组织。

### [naming_convention.md](02_naming_convention.md)
**文件命名规范**

说明项目的文件命名规则。

### [summary.md](01_summary.md)
**项目总结**

项目完成情况和关键改进点。

### [print_dict_logging.md](02_print_dict_logging.md)
**print_dict 日志功能说明**

详细说明 print_dict 函数的日志分级功能。

### [local_development.md](02_local_development.md)
**本地开发指南**

说明如何在本地安装和测试包。

### [python_version_upgrade.md](02_python_version_upgrade.md)
**Python 版本升级说明**

说明项目对 Python 版本的要求（3.10+）。

### [match_case_guide.md](02_match_case_guide.md)
**match-case 语法指南**

详细说明 Python 3.10+ 的 match-case 语法。

## 文档使用指南

### 对于新手

1. 首先阅读项目根目录的 [README.md](../README.md)
2. 查看 [upload_instructions.md](01_upload_instructions.md) 了解上传流程
3. 参考主教程: [../../how_to_publish_to_pypi.md](../../how_to_publish_to_pypi.md)

### 对于维护者

1. 发布新版本前查看 [release.md](01_release.md)
2. 发布后更新 [CHANGELOG.md](../CHANGELOG.md)
3. 使用 [../scripts/](../scripts/) 目录下的脚本自动化发布

### 对于贡献者

1. 提交 PR 时在 [CHANGELOG.md](../CHANGELOG.md) 中添加变更说明
2. 遵循版本号规范（语义化版本）
3. 确保所有测试通过

## 相关资源

- 主教程: [../../how_to_publish_to_pypi.md](../../how_to_publish_to_pypi.md)
- TestPyPI: https://test.pypi.org/
- PyPI: https://pypi.org/
- 语义化版本规范: https://semver.org/lang/zh-CN/

## 维护说明

### 更新 CHANGELOG.md
每次版本发布时：
1. 在文件顶部添加新版本
2. 使用清晰的分类（新增、改进、修复等）
3. 包含日期
4. 简洁描述每个变更

### 更新其他文档
- 当发布流程改变时，更新 release.md
- 当上传步骤改变时，更新 upload_instructions.md
- 保持文档与实际流程同步
