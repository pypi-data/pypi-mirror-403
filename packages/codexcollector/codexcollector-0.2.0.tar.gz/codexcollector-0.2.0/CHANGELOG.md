# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-19

### Changed
- **Breaking:** `collect()` now returns `list[Document]` instead of `dict[int, Document]`
- **Breaking:** `progress_callback` parameter changed from `Callable[[int, int], None] | None` to `int | None` (logs progress every N documents)
- **Breaking:** Removed `CorpusType` from public exports (use `list[Document]` directly)

### Added
- New `extract_page_text` parameter to extract text directly from HTML web pages
- HTML boilerplate removal (nav, header, footer, aside, scripts, styles)
- `html2text` dependency for cleaner HTML-to-text conversion

### Dependencies
- Added html2text>=2025.4.15

## [0.1.0] - 2024-12-13

### Added
- Initial release of CodexCollector
- Document collection from filesystem paths with recursive traversal
- Web scraping and document download with configurable crawling depth
- Support for multiple formats: Word (.docx, .doc), PowerPoint (.pptx, .ppt), PDF, plain text
- Automatic encoding detection for text files
- Metadata extraction (creation dates) where available
- Comprehensive error logging and graceful degradation
- Rate limiting and timeout controls for web requests
- File size validation and filtering
- Progress callbacks for large collections
- Configurable text encoding with fallback
- Collection timeout support
- TypedDict support for type safety

### Dependencies
- beautifulsoup4>=4.12.0
- chardet>=5.2.0
- docx2txt>=0.9
- pandas>=2.2.3
- pypdf>=5.1.0
- python-docx>=1.1.0
- python-pptx>=1.0.2
- requests>=2.32.0

[0.2.0]: https://github.com/NotAndroid37/codexcollector/releases/tag/v0.2.0
[0.1.0]: https://github.com/NotAndroid37/codexcollector/releases/tag/v0.1.0
