"""
基础 pytest 测试 - 包装现有测试脚本
"""

from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent


def test_simple_import():
    """测试基础导入功能"""
    # 测试基础模块导入
    import numpy
    import cv2
    from PIL import Image

    # 测试项目模块导入
    from svision.options import Options
    from svision import find_location, recognize_text

    # 基本断言
    assert numpy is not None
    assert cv2 is not None
    assert Image is not None
    assert Options is not None
    assert find_location is not None
    assert recognize_text is not None


def test_options_configuration():
    """测试 Options 配置"""
    from svision.options import Options

    # 测试默认配置
    assert hasattr(Options, "CV_THRESHOLD")
    assert hasattr(Options, "OCR_LANGUAGE")
    assert hasattr(Options, "OCR_USE_GPU")

    # 测试配置修改
    original_threshold = Options.CV_THRESHOLD
    Options.CV_THRESHOLD = 0.9
    assert Options.CV_THRESHOLD == 0.9

    # 恢复默认配置
    Options.reset_to_default()
    assert Options.CV_THRESHOLD == original_threshold


def test_cv_module_import():
    """测试 CV 模块导入"""
    from svision import find_location, find_all_locations
    from svision.aircv.cv import Template, match_loop

    assert find_location is not None
    assert find_all_locations is not None
    assert Template is not None
    assert match_loop is not None


def test_ocr_module_import():
    """测试 OCR 模块导入"""
    from svision.orc import TextRecognizer

    assert TextRecognizer is not None


def test_utils_import():
    """测试工具模块导入"""
    from svision.utils import logger

    assert logger is not None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
