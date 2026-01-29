# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial package structure
- Image classification module with PyTorch Lightning
- CLI interface with automatic fit+test workflow
- Support for folder-based and CSV-based datasets
- Configurable CNN architectures (simple, medium, deep, custom)
- Data augmentation support
- ONNX model export callback
- Comprehensive metrics (Accuracy, F1, Precision, Recall)

### Changed

### Fixed

### Deprecated

### Removed

### Security

---

## [0.1.0] - 2025-01-24

### Added
- Initial release of cph-imgclassification package
- PyTorch Lightning-based image classification pipeline
- Config-driven training workflow
- Automatic class detection from dataset
- Support for multiple CNN architectures
- ONNX model export for production deployment
- CLI command: `cph-imgclassification`
- Automatic fit+test workflow when no subcommand specified
- Support for standard Lightning CLI subcommands (fit, test, validate, predict)

### Features
- Fully config-driven via YAML files
- Generic and reusable for any image classification task
- Flexible data formats (folder-based and CSV)
- Auto-dimension detection
- Configurable CNN architectures
- Built-in data augmentation
- Production-ready ONNX export
- Comprehensive metrics tracking

[Unreleased]: https://github.com/imchandra11/cph-imgclassification/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/imchandra11/cph-imgclassification/releases/tag/v0.1.0
