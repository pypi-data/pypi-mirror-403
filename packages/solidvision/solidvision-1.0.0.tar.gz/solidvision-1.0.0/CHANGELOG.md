# Changelog

本文档记录 Supervision 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-01-26

### Added
- 🎉 首个正式版发布
- 🔍 图像模板匹配功能 (Template, match_loop)
- 📝 OCR 文字识别功能 (TextRecognizer, OCR)
- 🎯 便利函数 (find_location, find_text_position, get_all_text 等)
- 📊 完善的日志记录系统
- ⚙️ 配置管理系统 (Options, Config)

### Features
- 基于 PaddleOCR 的文字识别
- 基于 OpenCV 的图像模板匹配
- 支持多尺度模板匹配
- 支持关键点匹配算法
- 详细的日志输出和性能统计

### Documentation
- 完善的 API 文档
- 快速开始指南
- 示例代码

### CI/CD
- 使用 uv 构建系统
- GitHub Actions 自动化测试
- 自动发布到 PyPI

---

## 后续版本计划

### [1.1.0] - 计划中
- 更多图像预处理选项
- 支持更多 OCR 引擎
- 性能优化

### [1.2.0] - 计划中
- 支持批量图像处理
- 添加更多匹配算法
- GPU 加速支持
