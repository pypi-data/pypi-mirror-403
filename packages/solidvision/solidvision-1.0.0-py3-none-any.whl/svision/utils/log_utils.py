"""
日志工具模块 - 处理项目日志输出
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import colorlog
except ImportError:  # pragma: no cover - 可选依赖
    colorlog = None


class Logger:
    """项目日志管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = logging.getLogger("supervision")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # 清空现有的处理器
        self.logger.handlers.clear()

    @staticmethod
    def _enabled() -> bool:
        try:
            from svision.options import Options

            return bool(Options.LOG_ENABLED)
        except Exception:
            return True

    def _ensure_handlers(self) -> None:
        try:
            from svision.options import Options

            if not self._enabled():
                return

            if Options.LOG_CONSOLE:
                has_console = any(
                    isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
                    for h in self.logger.handlers
                )
                if not has_console:
                    level = getattr(logging, Options.LOG_LEVEL, logging.INFO)
                    self.set_console_handler(level=level, enabled=True)

            if Options.LOG_FILE:
                has_file = any(isinstance(h, logging.FileHandler) for h in self.logger.handlers)
                if not has_file:
                    level = getattr(logging, Options.LOG_LEVEL, logging.INFO)
                    self.set_file_handler(Options.LOG_PATH, level=level, enabled=True)
        except Exception:
            return

    @staticmethod
    def _short_text(text: str, max_len: int = 60) -> str:
        if len(text) <= max_len:
            return text
        return f"{text[: max_len - 3]}..."

    @staticmethod
    def _image_label(image: Any) -> str:
        if isinstance(image, Path):
            return image.name
        if isinstance(image, str):
            return os.path.basename(image)
        if hasattr(image, "shape"):
            return "ndarray"
        if hasattr(image, "size"):
            return "pil"
        return "unknown"

    def format_cv_detail(self, template: Any, image: Any) -> str:
        tmpl = self._image_label(template)
        img = self._image_label(image)
        return f"{tmpl} -> {img}"

    def format_ocr_image_detail(self, image: Any) -> str:
        return f"image={self._image_label(image)}"

    def format_ocr_text_detail(self, text: Any, found: Optional[Any] = None) -> str:
        src = self._short_text(str(text))
        if found is None:
            return f"text={src}"
        dst = self._short_text(str(found))
        return f"text={src} -> {dst}"

    def log_event(self, category: str, ok: bool, elapsed_ms: float, detail: str) -> None:
        if not self._enabled():
            return
        self._ensure_handlers()
        status = "OK" if ok else "NG"
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"{timestamp} | {category:<4} | {status:<2} | {elapsed_ms:>6.1f}ms | {detail}"
        if ok:
            self.logger.info(message)
        else:
            self.logger.error(message)

    def set_console_handler(self, level=logging.INFO, enabled=True):
        """设置控制台输出处理器"""
        # 移除旧的 console handler
        for h in self.logger.handlers[:]:
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout:
                self.logger.removeHandler(h)

        if not enabled:
            return

        # 添加新的 console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # 格式化输出
        if colorlog:
            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)-7s | %(message)s%(reset)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                },
            )
        else:
            formatter = logging.Formatter(
                "%(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def set_file_handler(self, filepath, level=logging.DEBUG, enabled=True):
        """设置文件输出处理器"""
        # 移除旧的 file handler
        for h in self.logger.handlers[:]:
            if isinstance(h, logging.FileHandler):
                self.logger.removeHandler(h)

        if not enabled or filepath is None:
            return

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # 添加新的 file handler
        file_handler = logging.FileHandler(filepath, encoding="utf-8")
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def debug(self, msg, *args, **kwargs):
        """Debug 级别日志"""
        if not self._enabled():
            return
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Info 级别日志"""
        if not self._enabled():
            return
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Warning 级别日志"""
        if not self._enabled():
            return
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Error 级别日志"""
        if not self._enabled():
            return
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Critical 级别日志"""
        if not self._enabled():
            return
        self.logger.critical(msg, *args, **kwargs)

    def section(self, title: str):
        """输出分隔标题"""
        if not self._enabled():
            return
        self.logger.info("=" * 60)
        self.logger.info(f"  {title}")
        self.logger.info("=" * 60)

    def subsection(self, title: str):
        """输出子标题"""
        if not self._enabled():
            return
        self.logger.info("")
        self.logger.info(f"[{title}]")
        self.logger.info("-" * 60)


# 全局 logger 实例
logger = Logger()
