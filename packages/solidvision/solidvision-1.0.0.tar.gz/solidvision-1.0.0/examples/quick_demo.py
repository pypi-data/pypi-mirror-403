# -*- coding: utf-8 -*-
"""solidvision SDK 使用示例"""

import sys
from pathlib import Path

import cv2

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from solidvision import find_location, find_text_position, recognize_text  # noqa: E402


def main():
    target_image = cv2.imread("test/assets/target.png")
    if target_image is None:
        raise RuntimeError("无法读取目标图像")

    # 模板匹配
    find_location(target_image, "test/assets/template1.png", threshold=0.8)

    # OCR 全量识别
    recognize_text(target_image)

    # 查找指定文本位置
    find_text_position(target_image, "控制台")


if __name__ == "__main__":
    main()
