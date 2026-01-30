# AGENTS.md
# 面向本仓库的代理协作说明（中文）

## 项目概览
- 仓库类型: Python 图像识别 + OCR 模块
- 运行环境: Python 3.12 (见 `pyproject.toml`)
- 依赖管理: `pyproject.toml` (使用 uv)
- 主要模块: `solidvision/aircv`, `solidvision/orc`, `solidvision/options`

## 本仓库显式规则
- 未发现 Cursor 规则: `.cursor/rules/` 或 `.cursorrules`
- 未发现 Copilot 规则: `.github/copilot-instructions.md`
- 默认遵循仓库约定与现有代码风格

## 安装与环境
- 推荐工具: `uv` (本仓库统一使用)
- 安装依赖:
  - `uv sync`        # 基础依赖
  - `uv sync --dev`  # 包含开发工具
- OCR 功能已包含，无需额外安装
- 本地可编辑安装 (可选):
  - `uv pip install -e .`

## 构建 / 运行命令
- 模块为纯 Python，无独立构建步骤
- 直接运行示例:
  - `uv run python examples/<script>.py`

## 测试命令
- pytest 入口 (CI 使用):
  - `uv run pytest`
  - `uv run pytest test`
- 单个测试文件:
  - `uv run pytest test/test_solidvision.py`
- 按关键字筛选 (pytest 适用):
  - `uv run pytest -k ocr`
- 说明:
  - `test/test_solidvision.py` 和 `test/simple_test.py` 主要是脚本式测试
  - 若 pytest 未收集到测试，可直接运行脚本:
    - `uv run python test/simple_test.py`
    - `uv run python test/test_solidvision.py`

## Lint / 代码质量
- CI workflow 使用命令 (当前仓库未提供根目录 Makefile):
  - `make check_code_quality`
- 如需本地 lint，建议临时安装并运行:
  - `uv pip install flake8`
  - `uv run python -m flake8 solidvision test`
- 若新增 lint 规则，请同步更新本文件

## 代码结构约定
- 包入口: `solidvision/__init__.py`
- 识别核心: `solidvision/aircv/*.py`
- OCR 核心: `solidvision/orc/__init__.py`
- 全局配置: `solidvision/options/__init__.py`
- 工具模块: `solidvision/utils/*.py`
- 测试资源: `test/assets`, 输出: `test/output`

## 代码风格与约定
- 文件编码: 大部分文件包含 `# -*- coding: utf-8 -*-`
- 文档语言: 中文为主，说明性注释保持简洁
- 模块级 docstring: 常见，建议保留
- 类命名: `PascalCase` (如 `TextRecognizer`, `Options`)
- 函数/变量: `snake_case`
- 常量: `UPPER_SNAKE_CASE` (如 `CV_THRESHOLD`, `OCR_LANGUAGE`)
- 私有/内部方法: 前缀 `_`
- 导入顺序:
  - 标准库 -> 第三方 -> 本地模块
  - 示例: `import os` / `import numpy as np` / `from solidvision...`
- 重复依赖: 优先复用已有工具类 (如 `solidvision.utils.logger`)

## 格式化与排版
- 未见自动格式化配置 (black/ruff/isort)
- 保持现有行宽与缩进风格:
  - 4 空格缩进
  - 空行分隔逻辑块
  - 长行可用括号或换行拆分
- 使用 f-string 格式化输出

## 类型提示
- 代码中有部分 `typing` 使用 (如 `List`, `Tuple`, `Dict`)
- 新增公共 API 建议补充类型注解
- 内部实现可简化，保持一致即可

## 日志与错误处理
- 统一使用 `solidvision.utils.logger` 输出日志
- 关键路径记录 `info`，异常用 `warning`/`error`
- 常见策略:
  - 输入不合法时返回 `None`
  - 可恢复错误使用 `try/except` 并记录日志
  - 结构性错误抛出 `ValueError`

## 配置管理
- 全局配置集中在 `Options` 类
- 建议通过 `Options.<KEY>` 修改参数
- 不要在多处定义重复配置常量
- 当修改配置默认值时，同步更新:
  - `Options.reset_to_default`
  - 文档或测试中的示例

## 资源与路径
- 路径推荐使用 `pathlib.Path`
- 测试资源使用相对路径:
  - `test/assets` / `test/output`
- 运行时路径需要时请使用 `Options.CURRENT_PATH`

## OCR 相关约定
- OCR 默认语言 `ch`
- GPU 配置默认开启但在测试中可改为 CPU
- 选择性关闭角度分类器以提升速度

## 变更注意事项
- 修改 API 导出时同步更新 `solidvision/__init__.py`
- 修改 OCR/CV 策略时注意 `Settings`/`Options` 的默认值
- 若新增依赖:
  - 更新 `pyproject.toml` 中的 `dependencies` 或 `project.optional-dependencies`

## 提交前建议
- 运行:
  - `uv run python test/simple_test.py`
  - `uv run pytest` (若 pytest 可收集)
- 检查示例和文档中的 API 是否仍然准确

## 常见入口速查
- 快速定位模板:
  - `from solidvision import find_location`
- OCR 识别:
  - `from solidvision import recognize_text, find_text_position`
- 统一配置:
  - `from solidvision.options import Options`
