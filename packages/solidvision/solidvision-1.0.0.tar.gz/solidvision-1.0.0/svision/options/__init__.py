# -*- coding: utf-8 -*-
"""
Options 模块 - 配置管理
用于管理全局配置选项
"""


class Options:
    """图像识别全局配置"""

    """**作者信息**"""
    AUTHOR = "caishilong"
    VERSION = "1.0.0"

    """**图像识别配置**"""
    """图像识别阈值（0-1），默认0.8"""
    CV_THRESHOLD = 0.8

    """查找图片超时时间（秒），默认10秒"""
    FIND_TIMEOUT = 10

    """**日志配置**"""
    """是否启用日志"""
    LOG_ENABLED = True

    """日志输出到控制台"""
    LOG_CONSOLE = True

    """日志输出到文件"""
    LOG_FILE = False

    """日志保存路径"""
    LOG_PATH = "test/test.log"

    """日志级别 (DEBUG, INFO, WARNING, ERROR)"""
    LOG_LEVEL = "INFO"

    """**OCR配置**"""
    """OCR语言包（中文/英文）"""
    OCR_LANGUAGE = "ch"

    """OCR使用GPU加速"""
    OCR_USE_GPU = True  # 启用 GPU 加速

    """OCR设备配置 (cpu, gpu:0, npu:0, xpu:0等)"""
    OCR_DEVICE = "gpu:0"  # 使用第一块 GPU

    """OCR启用高性能推理"""
    OCR_ENABLE_HPI = False

    """OCR使用TensorRT加速 (仅GPU)"""
    OCR_USE_TENSORRT = False

    """OCR精度 (fp32, fp16)"""
    OCR_PRECISION = "fp32"

    """OCR启用MKL-DNN优化 (仅CPU，Windows可能有兼容性问题)"""
    OCR_ENABLE_MKLDNN = False

    """OCR CPU线程数"""
    OCR_CPU_THREADS = 4

    """OCR使用方向分类器"""
    OCR_USE_ANGLE_CLS = False  # 禁用以提升速度

    """OCR模型下载/存储路径"""
    OCR_MODEL_DIR = None  # None 使用默认缓存，可设置自定义路径如 'models/ocr'

    """OCR使用轻量级模型 (mobile/serving)"""
    OCR_USE_MOBILE_MODEL = True  # 使用轻量级模型，速度更快

    """OCR禁用MKL-DNN (Windows兼容性)"""
    OCR_DISABLE_MKLDNN = True

    """**动态配置，由代码自动生成**"""
    """当前工作路径，用于相对路径引用"""
    CURRENT_PATH = ""

    @classmethod
    def reset_to_default(cls):
        """重置所有配置为默认值"""
        cls.CV_THRESHOLD = 0.8
        cls.FIND_TIMEOUT = 10
        cls.LOG_ENABLED = True
        cls.LOG_CONSOLE = True
        cls.LOG_FILE = False
        cls.LOG_PATH = "test/test.log"
        cls.LOG_LEVEL = "INFO"
        cls.OCR_LANGUAGE = "ch"
        cls.OCR_USE_GPU = True
        cls.OCR_DEVICE = "gpu:0"
        cls.OCR_ENABLE_HPI = False
        cls.OCR_USE_TENSORRT = False
        cls.OCR_PRECISION = "fp32"
        cls.OCR_ENABLE_MKLDNN = False
        cls.OCR_CPU_THREADS = 4
        cls.OCR_USE_ANGLE_CLS = False  # 禁用以提升速度
        cls.OCR_MODEL_DIR = None
        cls.OCR_USE_MOBILE_MODEL = True
        cls.CURRENT_PATH = ""

    @classmethod
    def get_config_dict(cls):
        """获取当前配置的字典表示"""
        return {
            "CV_THRESHOLD": cls.CV_THRESHOLD,
            "FIND_TIMEOUT": cls.FIND_TIMEOUT,
            "LOG_ENABLED": cls.LOG_ENABLED,
            "LOG_CONSOLE": cls.LOG_CONSOLE,
            "LOG_FILE": cls.LOG_FILE,
            "LOG_PATH": cls.LOG_PATH,
            "LOG_LEVEL": cls.LOG_LEVEL,
            "OCR_LANGUAGE": cls.OCR_LANGUAGE,
            "OCR_USE_GPU": cls.OCR_USE_GPU,
            "OCR_DEVICE": cls.OCR_DEVICE,
            "OCR_ENABLE_HPI": cls.OCR_ENABLE_HPI,
            "OCR_USE_TENSORRT": cls.OCR_USE_TENSORRT,
            "OCR_PRECISION": cls.OCR_PRECISION,
            "OCR_ENABLE_MKLDNN": cls.OCR_ENABLE_MKLDNN,
            "OCR_CPU_THREADS": cls.OCR_CPU_THREADS,
            "OCR_USE_ANGLE_CLS": cls.OCR_USE_ANGLE_CLS,
            "OCR_MODEL_DIR": cls.OCR_MODEL_DIR,
            "OCR_USE_MOBILE_MODEL": cls.OCR_USE_MOBILE_MODEL,
            "CURRENT_PATH": cls.CURRENT_PATH,
        }


# 为了兼容性，提供 Config 别名
Config = Options
