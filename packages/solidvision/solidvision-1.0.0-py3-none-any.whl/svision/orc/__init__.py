# -*- coding: utf-8 -*-
"""
OCR 模块 - PaddleOCR 封装
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_mkldnn", "0")

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from svision.options import Options
from svision.utils import logger


ImageInput = Union[str, np.ndarray, Image.Image]
OcrResult = Dict[str, Any]

_ocr_instance: Optional[PaddleOCR] = None


def _supports_param(param_name: str) -> bool:
    return True


def _resolve_image(image: ImageInput) -> Optional[np.ndarray]:
    if isinstance(image, np.ndarray):
        return image
    if isinstance(image, Image.Image):
        return np.array(image)
    if isinstance(image, str):
        try:
            import cv2
        except ImportError as exc:
            logger.error(f"缺少 cv2，无法读取图片路径: {exc}")
            return None
        return cv2.imread(image)
    return None


def _build_ocr_params() -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if _supports_param("lang"):
        params["lang"] = Options.OCR_LANGUAGE
    if _supports_param("use_angle_cls"):
        params["use_angle_cls"] = Options.OCR_USE_ANGLE_CLS
    if _supports_param("use_gpu"):
        params["use_gpu"] = Options.OCR_USE_GPU
    if _supports_param("device"):
        params["device"] = Options.OCR_DEVICE or "cpu"
    if _supports_param("enable_mkldnn"):
        params["enable_mkldnn"] = Options.OCR_ENABLE_MKLDNN
    if _supports_param("cpu_threads"):
        params["cpu_threads"] = Options.OCR_CPU_THREADS
    if _supports_param("use_tensorrt"):
        params["use_tensorrt"] = Options.OCR_USE_TENSORRT
    if _supports_param("precision"):
        params["precision"] = Options.OCR_PRECISION
    if _supports_param("use_space_char"):
        params["use_space_char"] = True
    if _supports_param("show_log"):
        params["show_log"] = False
    if _supports_param("ir_optim"):
        params["ir_optim"] = False
    return params


def _get_ocr_instance() -> PaddleOCR:
    global _ocr_instance
    if _ocr_instance is not None:
        return _ocr_instance
    params = _build_ocr_params()

    try:
        import paddle

        try:
            paddle.set_flags(
                {
                    "FLAGS_use_mkldnn": False,
                    "FLAGS_enable_mkldnn": False,
                }
            )
        except Exception as err:
            logger.warning(f"[OCR] 设置 MKLDNN 标志失败: {err}")

        if Options.OCR_USE_GPU:
            logger.info("[OCR] 设备设置为 GPU")
        else:
            logger.info("[OCR] 设备设置为 CPU")
    except Exception as err:
        logger.warning(f"[OCR] Paddle 初始化失败: {err}")

    logger.info("OCR model ready")
    _ocr_instance = PaddleOCR(**params)
    return _ocr_instance


def _parse_results(results: Sequence[Any]) -> List[OcrResult]:
    parsed: List[OcrResult] = []
    for line in results:
        if not line or len(line) < 2:
            continue
        box = line[0]
        text_info = line[1]
        if not text_info or len(text_info) < 2:
            continue
        text = text_info[0]
        confidence = float(text_info[1])
        xs = [point[0] for point in box]
        ys = [point[1] for point in box]
        center_x = int(sum(xs) / len(xs))
        center_y = int(sum(ys) / len(ys))
        parsed.append(
            {
                "text": text,
                "confidence": confidence,
                "position": (center_x, center_y),
                "box": box,
            }
        )
    return parsed


def _recognize_text(image: ImageInput, log: bool = True) -> List[OcrResult]:
    img = _resolve_image(image)
    if img is None:
        logger.error("OCR 输入图片无效")
        return []

    start = time.time()
    ocr = _get_ocr_instance()
    results = ocr.ocr(img, cls=Options.OCR_USE_ANGLE_CLS)
    if not results:
        if log:
            elapsed_ms = (time.time() - start) * 1000
            logger.log_event(
                "OCR",
                False,
                elapsed_ms,
                logger.format_ocr_image_detail(image),
            )
        return []

    # PaddleOCR 返回 [ [box, (text, conf)], ... ] 或 [ [ [box,...], ... ] ]
    if (
        results
        and isinstance(results[0], list)
        and results
        and results[0]
        and isinstance(results[0][0], list)
    ):
        parsed = _parse_results(results[0])
    else:
        parsed = _parse_results(results)

    if log:
        elapsed_ms = (time.time() - start) * 1000
        logger.log_event(
            "OCR",
            bool(parsed),
            elapsed_ms,
            logger.format_ocr_image_detail(image),
        )
    return parsed


def recognize_text(image: ImageInput) -> List[OcrResult]:
    return _recognize_text(image, log=True)


def find_text_position(image: ImageInput, target_text: str) -> Optional[Tuple[int, int]]:
    if not target_text:
        return None
    start = time.time()
    texts = _recognize_text(image, log=False)
    target = target_text.lower()
    for item in texts:
        text = str(item.get("text", "")).lower()
        if target in text or text in target:
            elapsed_ms = (time.time() - start) * 1000
            detail = logger.format_ocr_text_detail(target_text, item.get("text"))
            logger.log_event("OCR", True, elapsed_ms, detail)
            return item.get("position")
    elapsed_ms = (time.time() - start) * 1000
    logger.log_event(
        "OCR",
        False,
        elapsed_ms,
        logger.format_ocr_text_detail(target_text),
    )
    return None


def get_all_text(image: ImageInput) -> str:
    texts = recognize_text(image)
    return " ".join(item.get("text", "") for item in texts)


def clear_ocr_cache() -> None:
    global _ocr_instance
    _ocr_instance = None


class TextRecognizer:
    """OCR 识别器封装"""

    def __init__(self, lang: Optional[str] = None):
        if lang and lang != Options.OCR_LANGUAGE:
            logger.warning(f"OCR 已使用默认语言 {Options.OCR_LANGUAGE}，忽略传入的 {lang}")
        self._ocr = _get_ocr_instance()

    def recognize_image(self, image: ImageInput) -> List[OcrResult]:
        return recognize_text(image)

    def find_text_position(self, image: ImageInput, text: str) -> Optional[Tuple[int, int]]:
        return find_text_position(image, text)

    def get_page_text(self, image: ImageInput) -> str:
        return get_all_text(image)


OCR = TextRecognizer

__all__ = [
    "TextRecognizer",
    "OCR",
    "recognize_text",
    "find_text_position",
    "get_all_text",
    "clear_ocr_cache",
]
