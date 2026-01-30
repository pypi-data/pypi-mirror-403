# Supervision 1.0 正式版发布计划

## 项目概述

将 `solidvision` Python 包发布为正式的 1.0 版本到 PyPI，包括完整的配置更新和 CI/CD 流程。

## 当前状态分析

### 问题清单
1. **项目名称拼写**: `pyproject.toml` 中名称为 "supervison"（缺少 i），应为 "solidvision"
2. **版本号不一致**:
   - `pyproject.toml`: `version = "0.1.0"`
   - `solidvision/__init__.py`: `__version__ = "1.0.0"`
3. **CI/CD 配置过时**:
   - Python 版本矩阵使用 3.7-3.9，而项目要求 >=3.12
   - publish.yml 依赖不存在的 Makefile
   - 使用旧式的 pip 安装方式，应改用 uv
4. **缺少必要的元数据**:
   - 项目 URL
   - 作者信息
   - 许可证配置
   - 关键词
   - 分类器

---

## 发布步骤

### 第一阶段：项目配置修复

#### 1.1 修复 pyproject.toml

**文件**: [pyproject.toml](pyproject.toml)

**更新内容**:
```toml
[project]
name = "solidvision"  # 修正拼写
version = "1.0.0"  # 更新到 1.0

description = "图像识别与文字识别模块 - 轻量级独立 OCR/CV 模块"
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}  # 引用现有的 LICENSE 文件

# 作者信息
authors = [
    {name = "caishilong", email = "your-email@example.com"}
]

# 项目 URL
urls = {
    "Homepage" = "https://github.com/your-username/solidvision",
    "Repository" = "https://github.com/your-username/solidvision",
    "Bug Tracker" = "https://github.com/your-username/solidvision/issues",
}

# 关键词（用于 PyPI 搜索）
keywords = [
    "ocr",
    "opencv",
    "image-recognition",
    "text-recognition",
    "computer-vision",
    "paddleocr",
    "template-matching",
]

# PyPI 分类器
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Image Recognition",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "colorlog>=6.10.1",
    "logzero>=1.7.0",
    "matplotlib>=3.10.8",
    "numpy>=2.4.1",
    "opencv-contrib-python>=4.13.0.90",
    "paddleocr>=2.10.0",
    "paddlepaddle==2.6.2",
    "pillow>=12.1.0",
    "requests>=2.32.5",
]

# 可选依赖（用于开发和测试）
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.9.0",
    "mypy>=1.0.0",
]

# 构建系统
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Ruff 配置
[tool.ruff]
line-length = 100
target-version = "py312"

# Pytest 配置
[tool.pytest.ini_options]
testpaths = ["test"]
python_files = ["test_*.py"]
```

#### 1.2 更新版本管理

**文件**: [solidvision/__init__.py](solidvision/__init__.py)

**修改**:
- 将 `__version__ = "1.0.0"` 改为从 pyproject.toml 动态读取，或保持一致

---

### 第二阶段：CI/CD 流程现代化

#### 2.1 更新测试工作流

**文件**: [`.github/workflows/test.yml`](.github/workflows/test.yml)

**替换为**:
```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - name: 🛎️ Checkout
        uses: actions/checkout@v4

      - name: ⚡ Setup uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: 🐍 Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: 📦 Install dependencies
        run: |
          uv sync --dev

      - name: 🔍 Lint with ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: 🧪 Run tests
        run: |
          uv run pytest --cov=solidvision --cov-report=xml

      - name: 📊 Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### 2.2 更新发布工作流

**文件**: [`.github/workflows/publish.yml`](.github/workflows/publish.yml)

**替换为**:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]
  push:
    tags:
      - 'v*'

permissions:
  contents: read
  id-token: write  # Required for trusted publishing

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: 🛎️ Checkout
        uses: actions/checkout@v4

      - name: ⚡ Setup uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: 🔨 Build package
        run: |
          uv build

      - name: ✅ Check package
        run: |
          uv pip install twine
          twine check dist/*

      - name: 🚀 Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          skip-existing: true
```

#### 2.3 配置 PyPI Trusted Publishing

**需要执行的操作**:

1. 访问 https://pypi.org/manage/account/publishing/
2. 添加新的发布器：
   - **PyPI Project Name**: `solidvision`
   - **Owner**: 你的 GitHub 用户名
   - **Repository name**: `solidvision`
   - **Workflow name**: `publish.yml`
   - **Environment**: (留空)

---

### 第三阶段：发布前检查清单

#### 3.1 代码质量

- [ ] 所有测试通过: `uv run pytest`
- [ ] 代码格式化: `uv run ruff format .`
- [ ] 代码检查: `uv run ruff check . --fix`
- [ ] 类型检查（如使用）: `uv run mypy .`

#### 3.2 文档完善

- [ ] **README.md** 更新:
  - 清晰的项目描述
  - 安装说明
  - 快速开始示例
  - API 文档链接
  - 贡献指南

- [ ] **CHANGELOG.md** 创建:
  ```markdown
  # Changelog

  ## [1.0.0] - 2026-01-26

  ### Added
  - 图像模板匹配功能 (Template, match_loop)
  - OCR 文字识别功能 (TextRecognizer, OCR)
  - 便利函数 (find_location, find_text_position 等)
  - 完整的日志记录系统

  ### Documentation
  - 完善的 API 文档
  - 快速开始指南
  ```

- [ ] **MANIFEST.in** 检查（如需要）:
  ```ini
  include README.md
  include LICENSE
  recursive-include solidvision *.py
  ```

#### 3.3 版本一致性

- [ ] `pyproject.toml`: `version = "1.0.0"`
- [ ] `solidvision/__init__.py`: `__version__ = "1.0.0"`
- [ ] Git tag: 创建 `v1.0.0` 标签

#### 3.4 本地构建测试

```bash
# 使用 uv 构建包
uv build

# 检查包内容
tar -tzf dist/solidvision-1.0.0.tar.gz

# 本地安装测试
uv pip install -e .

# 或从 tar 安装测试
uv pip install dist/solidvision-1.0.0-py3-none-any.whl
```

---

### 第四阶段：发布执行

#### 4.1 创建 Git Tag

```bash
# 确保 main 分支是最新的
git checkout main
git pull

# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程
git push origin v1.0.0
```

#### 4.2 创建 GitHub Release

1. 访问 GitHub 仓库的 Releases 页面
2. 点击 "Draft a new release"
3. **Tag**: 选择 `v1.0.0`
4. **Title**: `v1.0.0 - 首个正式版`
5. **Description**:
   ```markdown
   ## 🎉 Supervision 1.0.0 - 首个正式版发布

   Supervision 是一个轻量级的图像识别与文字识别模块。

   ### ✨ 主要功能

   - 🔍 图像模板匹配
   - 📝 OCR 文字识别（基于 PaddleOCR）
   - 🎯 便利的查找函数
   - 📊 完善的日志系统

  ### 📦 安装

  ```bash
  pip install solidvision
  ```

  ### 🚀 快速开始

  ```python
  import solidvision

  # 图像识别
  position = solidvision.find_location(image, template_path)

  # OCR 识别
  text = solidvision.recognize_text(image)
  ```

  ### 📝 更新日志

  完整更新日志请查看 [CHANGELOG.md](CHANGELOG.md)
  ```
6. 点击 "Publish release"

#### 4.3 自动发布

- 推送 tag 或发布 Release 后，GitHub Actions 会自动：
  1. 构建包
  2. 发布到 PyPI

---

### 第五阶段：发布后验证

#### 5.1 PyPI 验证

```bash
# 安装发布的包
pip install solidvision==1.0.0

# 验证导入
python -c "import solidvision; print(solidvision.__version__)"

# 验证功能
python -c "from solidvision import find_location, OCR; print('导入成功')"
```

#### 5.2 访问 PyPI 页面

- 访问 https://pypi.org/project/solidvision/
- 确认所有信息显示正确
- 检查项目描述、关键词、分类器等

---

## 快速命令参考

```bash
# 本地开发
uv sync --dev                    # 安装依赖
uv run pytest                    # 运行测试
uv run ruff check . --fix        # 代码检查
uv run ruff format .             # 代码格式化

# 构建发布
uv build                          # 构建包
uv pip install twine              # 安装 twine
twine check dist/*               # 检查包

# 版本管理
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# 手动发布到测试 PyPI（可选）
uv pip install twine
twine upload --repository test dist/*

# 手动发布到正式 PyPI（如不使用 CI）
twine upload dist/*
```

---

## 注意事项

1. **项目名称**: 确认最终名称是 `solidvision`（修改拼写）
2. **PyPI 账户**: 需要注册 PyPI 账户并配置 Trusted Publishing
3. **测试**: 发布前在 TestPyPI 测试（可选但推荐）
4. **版本号**: 遵循语义化版本控制 (Semantic Versioning)
5. **依赖锁定**: 考虑是否需要固定某些依赖版本

---

## 后续维护

### 发布补丁版本 (1.0.1)

```bash
# 更新版本号
# pyproject.toml: version = "1.0.1"
# solidvision/__init__.py: __version__ = "1.0.1"

git add .
git commit -m "chore: bump version to 1.0.1"
git tag -a v1.0.1 -m "Release 1.0.1"
git push && git push origin v1.0.1
```

### 发布次要版本 (1.1.0)

遵循相同的流程，确保 CHANGELOG.md 更新了新功能说明。

---

## 文件清单

需要创建/修改的文件：

- [ ] [pyproject.toml](pyproject.toml) - 主要配置文件
- [ ] [solidvision/__init__.py](solidvision/__init__.py) - 版本号
- [ ] [README.md](README.md) - 项目文档
- [ ] [CHANGELOG.md](CHANGELOG.md) - 变更日志（新建）
- [ ] [`.github/workflows/test.yml`](.github/workflows/test.yml) - 测试工作流
- [ ] [`.github/workflows/publish.yml`](.github/workflows/publish.yml) - 发布工作流

---

## 附录：PyPI 配置 URL

- **PyPI 主页**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Trusted Publishing**: https://pypi.org/manage/account/publishing/
- **项目管理**: https://pypi.org/manage/account/projects/
