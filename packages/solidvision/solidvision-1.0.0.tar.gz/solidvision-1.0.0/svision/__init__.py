# -*- coding: utf-8 -*-
"""
Supervision - 图像识别与文字识别模块
一个轻量级的独立图像/文字识别模块，可集成到任何项目中
"""

__version__ = "1.0.0"
__author__ = "caishilong"

import time

# 导出主要类和函数
from svision.options import Options, Config
from svision.aircv.cv import Template, match_loop
from svision.orc import (
    TextRecognizer,
    OCR,
    recognize_text,
    find_text_position,
    get_all_text,
)
from svision.utils import logger


# 便利函数别名
def find_location(img, tmpl, **kw):
    """
    在图像中查找模板位置
    :param img: 目标图像（numpy数组）
    :param tmpl: 模板路径（字符串）
    :param kw: 其他参数
    :return: 匹配位置(x, y)或None
    """
    if not hasattr(img, "shape"):
        return None

    start = time.time()
    result = match_loop(lambda: img, tmpl, **kw)
    elapsed_ms = (time.time() - start) * 1000
    detail = logger.format_cv_detail(tmpl, img)
    logger.log_event("CV", bool(result), elapsed_ms, detail)
    return result


find_all_locations = find_location

__all__ = [
    # 配置
    "Options",
    "Config",
    # 图像识别
    "Template",
    "match_loop",
    "find_location",
    "find_all_locations",
    # 文字识别
    "TextRecognizer",
    "OCR",
    "recognize_text",
    "find_text_position",
    "get_all_text",
    # 版本信息
    "__version__",
    "__author__",
]
