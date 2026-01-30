# -*- coding: utf-8 -*-
"""
Supervision - 集成示例
展示如何将Supervision集成到不同的应用
"""

from solidvision import find_location
import cv2
import os


class DesktopAppIntegration:
    """
    桌面应用集成示例
    """

    def __init__(self, template_folder="templates"):
        self.recognizer = find_location()
        self.template_folder = template_folder

    def find_ui_element(self, screenshot, element_name):
        """
        在桌面应用截图中查找UI元素

        Args:
            screenshot: cv2 图像对象
            element_name: UI元素名称（对应模板文件名，不含扩展名）

        Returns:
            (x, y) 坐标或 None
        """
        template_path = os.path.join(self.template_folder, f"{element_name}.png")

        if not os.path.exists(template_path):
            print(f"警告: 模板文件不存在: {template_path}")
            return None

        position = self.recognizer.find_location(screenshot, template_path, threshold=0.8)

        return position

    def find_all_ui_elements(self, screenshot, element_name):
        """
        查找所有匹配的UI元素
        """
        template_path = os.path.join(self.template_folder, f"{element_name}.png")

        if not os.path.exists(template_path):
            print(f"警告: 模板文件不存在: {template_path}")
            return []

        positions = self.recognizer.find_all_locations(screenshot, template_path, threshold=0.8)

        return positions


class WebAppIntegration:
    """
    Web应用集成示例（使用Flask）
    """

    def __init__(self):
        self.recognizer = find_location()

    def recognize_from_bytes(self, image_bytes, template_path):
        """
        从字节数据进行识别

        Args:
            image_bytes: 图像二进制数据
            template_path: 模板文件路径

        Returns:
            识别结果 (x, y) 或 None
        """
        import numpy as np

        # 将字节转换为cv2图像
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            print("错误: 无法解码图像")
            return None

        position = self.recognizer.find_location(image, template_path, threshold=0.8)

        return position

    def recognize_from_url(self, image_url, template_path):
        """
        从URL加载图像并进行识别

        Args:
            image_url: 图像URL
            template_path: 模板文件路径

        Returns:
            识别结果或None
        """
        import requests

        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            image_bytes = response.content
            return self.recognize_from_bytes(image_bytes, template_path)

        except requests.RequestException as e:
            print(f"错误: 无法下载图像 - {e}")
            return None


class MobileAppIntegration:
    """
    移动应用集成示例
    """

    def __init__(self):
        self.recognizer = find_location()

    def recognize_from_screenshot(self, screenshot_path, template_path, threshold=0.8, timeout=10):
        """
        从截图文件进行识别

        Args:
            screenshot_path: 截图文件路径
            template_path: 模板文件路径
            threshold: 匹配阈值
            timeout: 超时时间

        Returns:
            识别结果或None
        """
        if not os.path.exists(screenshot_path):
            print(f"错误: 截图文件不存在 - {screenshot_path}")
            return None

        screenshot = cv2.imread(screenshot_path)

        if screenshot is None:
            print(f"错误: 无法读取截图文件 - {screenshot_path}")
            return None

        position = self.recognizer.find_location(
            screenshot, template_path, threshold=threshold, timeout=timeout
        )

        return position

    def find_multiple_elements(self, screenshot_path, template_path):
        """
        查找多个匹配元素
        """
        if not os.path.exists(screenshot_path):
            print(f"错误: 截图文件不存在 - {screenshot_path}")
            return []

        screenshot = cv2.imread(screenshot_path)

        if screenshot is None:
            print(f"错误: 无法读取截图文件 - {screenshot_path}")
            return []

        positions = self.recognizer.find_all_locations(screenshot, template_path, threshold=0.8)

        return positions


class RecognitionPipeline:
    """
    识别流程管理器
    一个完整的识别工作流示例
    """

    def __init__(self):
        self.recognizer = find_location()
        self.results = {}

    def add_task(self, task_name, screenshot, template_path):
        """
        添加识别任务
        """
        self.results[task_name] = {
            "screenshot": screenshot,
            "template": template_path,
            "status": "pending",
        }

    def run_all_tasks(self, threshold=0.8):
        """
        运行所有识别任务
        """
        for task_name, task_data in self.results.items():
            try:
                position = self.recognizer.find_location(
                    task_data["screenshot"], task_data["template"], threshold=threshold
                )

                if position:
                    self.results[task_name]["status"] = "success"
                    self.results[task_name]["position"] = position
                else:
                    self.results[task_name]["status"] = "not_found"
                    self.results[task_name]["position"] = None

            except Exception as e:
                self.results[task_name]["status"] = "error"
                self.results[task_name]["error"] = str(e)

    def get_results(self):
        """
        获取所有结果
        """
        return self.results

    def print_summary(self):
        """
        打印结果摘要
        """
        print("=" * 50)
        print("识别任务摘要")
        print("=" * 50)

        for task_name, task_data in self.results.items():
            status = task_data["status"]

            if status == "success":
                print(f"✓ {task_name}: {task_data['position']}")
            elif status == "not_found":
                print(f"✗ {task_name}: 未找到匹配")
            elif status == "error":
                print(f"✗ {task_name}: 错误 - {task_data.get('error')}")
            else:
                print(f"⚠ {task_name}: 待执行")


# 使用示例
if __name__ == "__main__":
    print("图像识别模块 - 集成示例")
    print("=" * 50)

    # 示例1: 桌面应用集成
    print("\n示例1: 桌面应用集成")
    print("-" * 50)
    desktop_app = DesktopAppIntegration(template_folder="templates")
    print("✓ 桌面应用集成器已创建")
    print("  使用方法: position = desktop_app.find_ui_element(screenshot, 'button')")

    # 示例2: Web应用集成
    print("\n示例2: Web应用集成")
    print("-" * 50)
    web_app = WebAppIntegration()
    print("✓ Web应用集成器已创建")
    print("  使用方法: position = web_app.recognize_from_bytes(image_bytes, 'template.png')")

    # 示例3: 移动应用集成
    print("\n示例3: 移动应用集成")
    print("-" * 50)
    mobile_app = MobileAppIntegration()
    print("✓ 移动应用集成器已创建")
    print(
        "  使用方法: position = mobile_app.recognize_from_screenshot('screenshot.png', 'template.png')"
    )

    # 示例4: 识别流程管理
    print("\n示例4: 识别流程管理")
    print("-" * 50)
    pipeline = RecognitionPipeline()
    print("✓ 识别流程管理器已创建")
    print("  使用方法: pipeline.add_task('task_name', screenshot, 'template.png')")
    print("           pipeline.run_all_tasks()")

    print("\n" + "=" * 50)
