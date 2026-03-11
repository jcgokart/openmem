# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.1] - 2026-03-10

### Added
- Project-level Memory support (independent memory space per project)
- Global/Project layers (flexible like Poetry)
- Template initialization (minimal/standard/full)
- Configuration inheritance system (supports extends global config)
- Auto-generate rules file (adapted for Trae/VS Code)
- Chinese tokenization search (jieba + FTS5)
- BM25 relevance ranking
- Encrypted backup feature
- Version control (Git-like)
- Smart trigger

### Changed
- Refactored to modular architecture (storage/core/features/cli)
- Windows path compatibility fixes

### Fixed
- Default project path handling
- Windows path slash mixing issue

## [1.0.0] - 2024-01-01

### Added
- Initial version
- Basic Memory functionality
