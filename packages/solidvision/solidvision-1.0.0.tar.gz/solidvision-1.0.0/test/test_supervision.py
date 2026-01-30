"""
Supervision 图像识别与OCR测试框架
包含模板匹配测试和文字识别测试 - 使用 logger 管理日志输出
"""

import sys
import time
from datetime import datetime
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Any, Optional

from PIL import Image, ImageDraw, ImageFont

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from svision import (  # noqa: E402
    find_location,
    recognize_text,
)
from svision.options import Options  # noqa: E402
from svision.utils import logger  # noqa: E402
import logging  # noqa: E402


class TestConfig:
    """测试配置"""

    # 目录配置
    ASSETS_DIR = project_root / "test" / "assets"
    OUTPUT_DIR = project_root / "test" / "output"

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 测试图像
    TARGET_IMAGE = ASSETS_DIR / "target.png"
    TEMPLATES = [
        ASSETS_DIR / "template1.png",
        ASSETS_DIR / "template2.png",
        ASSETS_DIR / "template3.png",
    ]

    # 识别参数
    CV_THRESHOLD = 0.8
    OCR_THRESHOLD = 0.7

    # 绘图参数
    RECT_COLOR = (0, 255, 0)  # 绿色
    CIRCLE_COLOR = (255, 0, 0)  # 蓝色
    TEXT_COLOR = (0, 0, 255)  # 红色
    RECT_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.6
    FONT_THICKNESS = 1

    # 提取的UI文本（从截图中）
    OCR_TEST_TEXTS = [
        "火山方舟",  # 大标题
        "一站式大模型服务平台",  # 副标题
        "立即体验",  # 按钮
        "控制台",  # 按钮
        "模型能力拓展",  # 功能
        "专业孪生服务",  # 功能
        "安全可信合话选言",  # 功能
        "品开发孪生保障",  # 功能
    ]


class CVTestResult:
    """CV测试结果"""

    def __init__(
        self,
        template_name: str,
        position: Optional[Tuple[int, int]],
        matched: bool,
        template_size: Tuple[int, int],
    ):
        self.template_name = template_name
        self.position = position
        self.matched = matched
        self.template_size = template_size
        self.type = "CV_MATCH"

    def get_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """获取边界框 (x1, y1, x2, y2)"""
        if not self.position:
            return None
        x, y = self.position
        w, h = self.template_size
        return (x - w // 2, y - h // 2, x + w // 2, y + h // 2)


class OCRTestResult:
    """OCR测试结果"""

    def __init__(
        self,
        text: str,
        position: Tuple[int, int],
        confidence: float,
        box: Optional[List[Tuple[int, int]]] = None,
    ):
        self.text = text
        self.position = position
        self.confidence = confidence
        self.box = box
        self.type = "OCR_TEXT"

    def __repr__(self):
        return f"OCR('{self.text}' @ {self.position}, conf={self.confidence:.2f})"


class TestExecutor:
    """测试执行器"""

    def __init__(self):
        self.cv_results: List[CVTestResult] = []
        self.ocr_results: List[OCRTestResult] = []
        self.target_image = None
        self.result_image = None

        # 使用默认中文模型并启用 GPU
        Options.OCR_LANGUAGE = "ch"
        Options.OCR_USE_GPU = True
        Options.OCR_DEVICE = "gpu:0"

        # 初始化 logger
        self._init_logger()

    def _init_logger(self):
        """初始化日志"""
        if Options.LOG_ENABLED:
            log_level = getattr(logging, Options.LOG_LEVEL, logging.INFO)

            if Options.LOG_CONSOLE:
                logger.set_console_handler(level=log_level, enabled=True)

            if Options.LOG_FILE:
                logger.set_file_handler(Options.LOG_PATH, level=logging.DEBUG, enabled=True)

    @staticmethod
    def _get_chinese_font(size: int = 18) -> Any:
        font_paths = [
            r"C:\\Windows\\Fonts\\msyh.ttc",
            r"C:\\Windows\\Fonts\\simhei.ttf",
            r"C:\\Windows\\Fonts\\simsun.ttc",
        ]
        for path in font_paths:
            if Path(path).exists():
                return ImageFont.truetype(path, size=size)
        return ImageFont.load_default()

    @staticmethod
    def _short_value(value: Any) -> str:
        if isinstance(value, Path):
            text = value.name
        else:
            text = str(value)
        if len(text) > 60:
            text = f"{text[:57]}..."
        return text

    def _log_event(
        self,
        category: str,
        ok: bool,
        elapsed_ms: float,
        detail: str,
    ):
        status = "OK" if ok else "NG"
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"{timestamp} | {category:<4} | {status:<2} | {elapsed_ms:>6.1f}ms | {detail}"
        if ok:
            logger.info(message)
        else:
            logger.error(message)

    def load_target_image(self) -> bool:
        """加载目标图像"""
        if not TestConfig.TARGET_IMAGE.exists():
            logger.error(f"目标图像不存在: {TestConfig.TARGET_IMAGE}")
            return False

        self.target_image = cv2.imread(str(TestConfig.TARGET_IMAGE))
        if self.target_image is None:
            logger.error(f"无法读取目标图像: {TestConfig.TARGET_IMAGE}")
            return False

        # 复制一份用于绘图
        self.result_image = self.target_image.copy()
        self._log_event(
            "LOAD",
            True,
            0,
            f"image={self._short_value(TestConfig.TARGET_IMAGE)}",
        )
        return True

    def test_template_matching(self) -> bool:
        """测试模板匹配"""
        success_count = 0

        for i, template_path in enumerate(TestConfig.TEMPLATES, 1):
            if not template_path.exists():
                logger.warning(f"模板{i}不存在: {template_path}")
                continue

            template = cv2.imread(str(template_path))
            if template is None:
                logger.warning(f"无法读取模板{i}: {template_path}")
                continue

            template_name = template_path.stem
            template_size = (template.shape[1], template.shape[0])

            match_start = time.time()

            # 执行匹配
            try:
                position = find_location(
                    self.target_image,
                    str(template_path),
                    threshold=TestConfig.CV_THRESHOLD,
                )
                elapsed_ms = (time.time() - match_start) * 1000
                detail = (
                    f"{self._short_value(template_path)} -> "
                    f"{self._short_value(TestConfig.TARGET_IMAGE)}"
                )

                if position:
                    result = CVTestResult(template_name, position, True, template_size)
                    self.cv_results.append(result)
                    success_count += 1
                    self._log_event("CV", True, elapsed_ms, detail)
                else:
                    result = CVTestResult(template_name, None, False, template_size)
                    self.cv_results.append(result)
                    self._log_event("CV", False, elapsed_ms, detail)

            except Exception as e:
                logger.error(f"模板匹配错误: {template_name} - {e}")
                result = CVTestResult(template_name, None, False, template_size)
                self.cv_results.append(result)

        return success_count >= len(TestConfig.TEMPLATES) // 2

    def test_ocr_recognition(self) -> bool:
        """测试OCR识别"""
        if self.target_image is None:
            logger.error("未加载目标图像，无法进行OCR")
            return False

        success_count = 0
        total = len(TestConfig.OCR_TEST_TEXTS)

        try:
            # 测试每个预期的文字
            for i, target_text in enumerate(TestConfig.OCR_TEST_TEXTS, 1):
                text_start = time.time()
                all_texts = recognize_text(self.target_image)

                # 尝试精确匹配
                found = False
                found_item = None

                for item in all_texts:
                    if (
                        target_text.lower() in item["text"].lower()
                        or item["text"].lower() in target_text.lower()
                    ):
                        found = True
                        found_item = item
                        break

                text_elapsed = (time.time() - text_start) * 1000
                if found and found_item:
                    result = OCRTestResult(
                        found_item["text"],
                        found_item["position"],
                        found_item["confidence"],
                        box=found_item.get("box"),
                    )
                    self.ocr_results.append(result)
                    detail = (
                        f"text={self._short_value(target_text)} -> "
                        f"{self._short_value(found_item['text'])}"
                    )
                    self._log_event("OCR", True, text_elapsed, detail)
                    success_count += 1
                else:
                    detail = f"text={self._short_value(target_text)}"
                    self._log_event("OCR", False, text_elapsed, detail)

            return success_count >= int(total * 0.6)  # 至少60%成功率

        except Exception as e:
            logger.error(f"OCR测试错误: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def draw_results(self):
        """在结果图上绘制识别结果"""
        if self.result_image is None:
            logger.error("未加载目标图像，无法绘制结果")
            return

        # 绘制CV匹配结果
        for result in self.cv_results:
            if not result.matched or not result.position:
                continue

            bbox = result.get_bbox()
            if bbox:
                x1, y1, x2, y2 = bbox
                # 绘制矩形
                cv2.rectangle(
                    self.result_image,
                    (x1, y1),
                    (x2, y2),
                    TestConfig.RECT_COLOR,
                    TestConfig.RECT_THICKNESS,
                )

                # 绘制文字标签
                label = f"CV:{result.template_name}"
                label_size = cv2.getTextSize(
                    label,
                    TestConfig.FONT,
                    TestConfig.FONT_SCALE,
                    TestConfig.FONT_THICKNESS,
                )[0]
                label_y = max(y1 - 5, label_size[1] + 5)

                # 背景
                cv2.rectangle(
                    self.result_image,
                    (x1, label_y - label_size[1] - 5),
                    (x1 + label_size[0] + 5, label_y + 5),
                    TestConfig.RECT_COLOR,
                    -1,
                )

                # 文字
                cv2.putText(
                    self.result_image,
                    label,
                    (x1 + 2, label_y - 2),
                    TestConfig.FONT,
                    TestConfig.FONT_SCALE,
                    (255, 255, 255),
                    TestConfig.FONT_THICKNESS,
                )

        # 绘制OCR识别结果
        if self.ocr_results:
            pil_image = Image.fromarray(cv2.cvtColor(self.result_image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            font = self._get_chinese_font(size=18)

            for result in self.ocr_results:
                x, y = result.position

                if result.box:
                    draw.line(
                        result.box + [result.box[0]],
                        fill=TestConfig.CIRCLE_COLOR,
                        width=2,
                    )
                else:
                    cv2.circle(self.result_image, (x, y), 8, TestConfig.CIRCLE_COLOR, 2)

                label = f"OCR:{result.text}({result.confidence:.0%})"
                text_box = draw.textbbox((0, 0), label, font=font)
                text_w = text_box[2] - text_box[0]
                text_h = text_box[3] - text_box[1]
                label_x = max(0, x - text_w // 2)
                label_y = max(0, y - text_h - 12)

                draw.rectangle(
                    [
                        (label_x - 4, label_y - 2),
                        (label_x + text_w + 4, label_y + text_h + 2),
                    ],
                    fill=TestConfig.CIRCLE_COLOR,
                )
                draw.text((label_x, label_y), label, fill=(255, 255, 255), font=font)

            self.result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def save_results(self):
        """保存结果"""
        if self.result_image is None:
            logger.error("未加载目标图像，无法保存结果")
            return

        output_path = TestConfig.OUTPUT_DIR / "result_annotated.png"
        cv2.imwrite(str(output_path), self.result_image)
        self._log_event(
            "SAVE",
            True,
            0,
            f"file={self._short_value(output_path)}",
        )

        # 生成测试报告
        report_path = TestConfig.OUTPUT_DIR / "test_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Supervision 测试报告\n")
            f.write("=" * 60 + "\n\n")

            f.write("[OCR 配置信息]\n")
            f.write(f"  语言: {Options.OCR_LANGUAGE}\n")
            f.write(f"  设备: {Options.OCR_DEVICE or 'auto'}\n")
            f.write(f"  GPU: {Options.OCR_USE_GPU}\n")
            f.write(f"  方向分类器: {Options.OCR_USE_ANGLE_CLS}\n")
            f.write(f"  高性能推理: {Options.OCR_ENABLE_HPI}\n")
            f.write(f"  TensorRT: {Options.OCR_USE_TENSORRT}\n")
            f.write(f"  精度: {Options.OCR_PRECISION}\n")
            f.write(f"  MKL-DNN: {Options.OCR_ENABLE_MKLDNN}\n")
            f.write(f"  CPU线程: {Options.OCR_CPU_THREADS}\n\n")

            f.write("[CV 模板匹配测试结果]\n")
            for result in self.cv_results:
                status = "成功" if result.matched else "失败"
                f.write(f"{status}: {result.template_name}\n")
                if result.position:
                    f.write(f"  位置: {result.position}\n")
                f.write(f"  大小: {result.template_size[0]}x{result.template_size[1]}\n\n")

            f.write(
                f"\nCV 总体: {sum(1 for r in self.cv_results if r.matched)}/{len(self.cv_results)}\n\n"
            )

            f.write("[OCR 文字识别测试结果]\n")
            for result in self.ocr_results:
                f.write(f"识别: '{result.text}'\n")
                f.write(f"  位置: {result.position}\n")
                f.write(f"  置信度: {result.confidence:.2%}\n\n")

            f.write(f"\nOCR 总体: {len(self.ocr_results)} 个文本\n")

        self._log_event(
            "SAVE",
            True,
            0,
            f"file={self._short_value(report_path)}",
        )

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        # 加载目标图像
        if not self.load_target_image():
            return False

        # 运行测试
        cv_ok = self.test_template_matching()
        ocr_ok = self.test_ocr_recognition()

        # 绘制结果
        self.draw_results()

        # 保存结果
        self.save_results()

        # 总结
        logger.info(f"CV 测试: {'通过' if cv_ok else '部分通过'}")
        logger.info(f"OCR 测试: {'通过' if ocr_ok else '部分通过'}")
        logger.info(f"总体结果: {'全部通过' if cv_ok and ocr_ok else '需要改进'}")

        return cv_ok and ocr_ok


def main():
    """主函数"""
    executor = TestExecutor()
    success = executor.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
