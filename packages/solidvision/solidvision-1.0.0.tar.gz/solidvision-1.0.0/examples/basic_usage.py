# -*- coding: utf-8 -*-
"""
solidvision 图像识别模块 - 基础示例
演示如何使用图像识别功能
"""

import cv2
import os
from solidvision import find_location, find_all_locations, Config, Template


def example_basic_usage():
    """
    示例1：基础使用 - 查找单个模板
    """
    print("=== 示例1: 基础使用 ===")

    # 读取截图
    screenshot_path = "screenshot.png"
    template_path = "template.png"

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 读取图像
    screenshot = cv2.imread(screenshot_path)

    # 使用便捷函数查找模板
    position = find_location(screenshot, template_path, threshold=0.8)

    if position:
        print(f"✓ 找到匹配: {position}")
    else:
        print("✗ 未找到匹配")


def example_all_locations():
    """
    示例2: 查找所有匹配位置
    """
    print("\n=== 示例2: 查找所有匹配位置 ===")

    screenshot_path = "screenshot.png"
    template_path = "template.png"

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 读取图像
    screenshot = cv2.imread(screenshot_path)

    # 查找所有匹配
    position = find_all_locations(screenshot, template_path, threshold=0.75)

    if position:
        print(f"✓ 找到匹配: {position}")
    else:
        print("✗ 未找到任何匹配")


def example_template_usage():
    """
    示例3: 使用 Template 类
    """
    print("\n=== 示例3: 使用 Template 类 ===")

    screenshot_path = "screenshot.png"
    template_path = "template.png"

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 创建模板实例
    template = Template(template_path, threshold=0.8)

    # 读取图像
    screenshot = cv2.imread(screenshot_path)

    # 查找匹配
    position = template.match_in_image(screenshot)

    if position:
        print(f"✓ 找到匹配: {position}")
    else:
        print("✗ 未找到匹配")


def example_multiple_templates():
    """
    示例4: 识别多个不同的模板
    """
    print("\n=== 示例4: 识别多个模板 ===")

    screenshot_path = "screenshot.png"
    templates = ["button1.png", "button2.png", "button3.png"]

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 读取图像
    screenshot = cv2.imread(screenshot_path)

    # 识别每个模板
    for template in templates:
        if os.path.exists(template):
            position = find_location(screenshot, template, threshold=0.8)
            if position:
                print(f"✓ {template}: {position}")
            else:
                print(f"✗ {template}: 未找到")
        else:
            print(f"⚠ {template}: 文件不存在")


def example_config_usage():
    """
    示例5: 使用配置调整识别参数
    """
    print("\n=== 示例5: 配置调整 ===")

    # 修改全局配置
    Config.CV_THRESHOLD = 0.85
    Config.FIND_TIMEOUT = 15
    Config.SAVE_LOG = True

    print("✓ 配置已更新:")
    print(f"  CV_THRESHOLD: {Config.CV_THRESHOLD}")
    print(f"  FIND_TIMEOUT: {Config.FIND_TIMEOUT}")
    print(f"  SAVE_LOG: {Config.SAVE_LOG}")


def example_with_threshold():
    """
    示例6: 使用不同的阈值
    """
    print("\n=== 示例6: 阈值调整 ===")

    screenshot_path = "screenshot.png"
    template_path = "template.png"

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 读取图像
    screenshot = cv2.imread(screenshot_path)

    # 使用不同的阈值进行识别
    thresholds = [0.7, 0.8, 0.9]

    for threshold in thresholds:
        position = find_location(screenshot, template_path, threshold=threshold)
        if position:
            print(f"✓ 阈值 {threshold}: 找到 {position}")
        else:
            print(f"✗ 阈值 {threshold}: 未找到")


def example_advanced_matching():
    """
    示例7: 高级匹配配置
    """
    print("\n=== 示例7: 高级匹配配置 ===")

    from solidvision.aircv.settings import Settings

    screenshot_path = "screenshot.png"
    template_path = "template.png"

    if not os.path.exists(screenshot_path):
        print(f"请确保 {screenshot_path} 存在")
        return

    # 配置匹配策略
    Settings.CVSTRATEGY = ("tpl", "gmstpl", "kaze", "brisk")

    # 创建模板对象
    template = Template(template_path, threshold=0.8)

    print("✓ 高级配置:")
    print(f"  匹配策略: {Settings.CVSTRATEGY}")
    print(f"  模板阈值: {template.threshold}")


def example_integration():
    """
    示例8: 集成示例 - 如何集成到你的应用
    """
    print("\n=== 示例8: 集成示例 ===")

    code = """
# 集成到桌面应用示例
import cv2
import pyautogui
import numpy as np
from solidvision import find_location

def get_desktop_screenshot():
    '''获取桌面截图'''
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_button_on_desktop(template_path):
    '''在桌面上查找按钮'''
    screenshot = get_desktop_screenshot()
    position = find_location(screenshot, template_path)

    if position:
        x, y = position
        print(f"找到按钮: ({x}, {y})")
        # 在桌面应用中可以进行后续操作，如点击
        return position
    else:
        print("未找到按钮")
        return None

# 使用示例
if __name__ == '__main__':
    button_pos = find_button_on_desktop('button.png')
    if button_pos:
        # 进行点击或其他操作
        pyautogui.click(button_pos)
    """

    print(code)


def main():
    """
    运行所有示例
    """
    print("=" * 50)
    print("图像识别模块 - 使用示例")
    print("=" * 50)

    # 运行示例
    example_basic_usage()
    example_all_locations()
    example_template_usage()
    example_multiple_templates()
    example_config_usage()
    example_with_threshold()
    example_advanced_matching()
    example_integration()

    print("\n" + "=" * 50)
    print("示例运行完毕")
    print("=" * 50)


if __name__ == "__main__":
    main()
