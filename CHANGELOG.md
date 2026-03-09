# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2024-03-09

### Added
- 项目级 Memory 支持（每个项目独立记忆空间）
- 全局/项目分层（类似 Poetry 灵活模式）
- 模板化初始化（minimal/standard/full）
- 配置继承系统（支持 extends 全局配置）
- 规则文件自动生成（适配 Trae/VS Code）
- 中文分词搜索（jieba + FTS5）
- BM25 相关性排序
- 加密备份功能
- 版本控制（Git-like）
- 智能触发器

### Changed
- 重构为模块化架构（storage/core/features/cli）
- Windows 路径兼容性修复

### Fixed
- 默认项目路径处理
- Windows 路径斜杠混用问题

## [1.0.0] - 2024-01-01

### Added
- 初始版本
- 基础 Memory 功能
