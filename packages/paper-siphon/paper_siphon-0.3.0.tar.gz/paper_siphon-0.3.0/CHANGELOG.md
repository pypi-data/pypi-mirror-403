# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-01-25

### Added

- `--version` flag to display current version

## [0.2.0] - 2025-01-24

### Added

- URL support: download and convert PDFs directly from URLs
- Show help text when invoked with no arguments

### Fixed

- arXiv-style filenames (e.g., `1706.03762`) now produce correct output (`1706.03762.md` instead of `1706.md`)

## [0.1.0] - 2025-01-14

### Added

- Initial release
- PDF to Markdown extraction using Docling
- Line number removal for academic papers
- Whitespace normalization
- VLM pipeline support for complex layouts
- MLX acceleration for Apple Silicon
- Formula enrichment option

[Unreleased]: https://github.com/mrshu/paper-siphon/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/mrshu/paper-siphon/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mrshu/paper-siphon/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mrshu/paper-siphon/releases/tag/v0.1.0
