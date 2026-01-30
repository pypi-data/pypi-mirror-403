#!/usr/bin/env python
"""
简单的项目测试脚本 - 验证项目环境
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("📦 solidvision 项目测试")
print("=" * 60)
print()

# 测试导入
print("✓ 测试 1: 导入基础模块")
try:
    import numpy

    print(f"  ✅ numpy {numpy.__version__}")
except ImportError as e:
    print(f"  ❌ numpy: {e}")

try:
    import cv2

    print(f"  ✅ opencv {cv2.__version__}")
except ImportError as e:
    print(f"  ❌ opencv: {e}")

try:
    from PIL import Image

    _ = Image  # 标记为有意未使用
    print("  ✅ PIL")
except ImportError as e:
    print(f"  ❌ PIL: {e}")

print()
print("✓ 测试 2: 导入项目模块")

try:
    from svision.options import Options

    _ = Options  # noqa: F401
    print("  ✅ svision.options")
except ImportError as e:
    print(f"  ❌ svision.options: {e}")

try:
    from svision.aircv import aircv as aircv_module

    _ = aircv_module  # noqa: F401
    print("  ✅ svision.aircv")
except ImportError as e:
    print(f"  ❌ svision.aircv: {e}")

try:
    from svision.orc import TextRecognizer

    _ = TextRecognizer  # noqa: F401
    print("  ✅ svision.orc")
except ImportError as e:
    print(f"  ❌ svision.orc: {e}")

print()
print("✓ 测试 3: 检查测试资源")

test_assets = project_root / "test" / "assets"
if test_assets.exists():
    files = list(test_assets.glob("*.png"))
    print(f"  ✅ 测试资源目录存在 ({len(files)} 个图像文件)")
else:
    print("  ❌ 测试资源目录不存在")

print()
print("=" * 60)
print("✅ 环境检查完成")
print("=" * 60)
