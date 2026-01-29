# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-01-24

### Added
- Fully configurable subtitle styling across YAML, CLI, and environment settings
- Subtitle enable/disable toggle and words-per-line control
- ASS alignment mapping for subtitle positioning

### Changed
- Normalize subtitle colors from hex to ASS format during generation
- Apply subtitle highlight color to karaoke-style rendering

## [0.3.0] - 2026-01-24

### Added
- **Pixabay Code Support**: Added Pixabay as an alternative stock footage provider alongside Pexels.
- **Configurable Provider**: New `stock_provider` configuration option to switch between generic stock providers.
- **Provider-Agnostic Models**: Refactored internal video models to support multiple providers seamlessly.

### Changed
- Refactored `PexelsService` to inherit from a common base class, sharing validation logic with `PixabayService`.
- Renamed `PexelsVideo` to `StockVideo` and `PexelsVideoFile` to `StockVideoFile` to reflect the multi-provider architecture.

## [0.2.0] - 2026-01-23

### Added
- Smart keyword fallback with AI-generated alternative search terms when stock footage search fails
- New `generate_alternative_keyword()` method in OpenAI service for intelligent keyword suggestions
- Enhanced error messages with list of tried keywords for debugging

### Changed
- Increased default `max_retries` from 3 to 5 for more reliable API interactions
- Batch processor now properly uses `CompositionResult` API for better result handling
- Improved stock footage validation loop with nested retry logic per keyword

### Fixed
- Batch processor parameter naming (`context` → `validation_context`, `keep_temp` → `cleanup_temp`)

## [0.1.0] - 2026-01-23

### Added
- Initial release of Video Composer
- AI-powered voiceover generation using OpenAI TTS (tts-1-hd model)
- Word-level transcription with OpenAI Whisper
- AI video validation using GPT-4 Vision to ensure footage relevance
- Automatic stock footage fetching from Pexels API
- Karaoke-style animated subtitles in ASS format
- 9:16 vertical video output optimized for TikTok, YouTube Shorts, and Instagram Reels
- Rich CLI with progress indicators and beautiful output
- YAML configuration support for single and batch video generation
- Multiple CLI commands:
  - `create` - Create marketing videos from script and keywords
  - `tts` - Generate text-to-speech audio only
  - `transcribe` - Transcribe audio with word-level timestamps
  - `search-footage` - Search and download stock footage
  - `from-yaml` - Generate videos from YAML configuration
  - `init-config` - Create sample YAML configuration templates
  - `config` - Display current configuration
  - `version` - Show version information
- Environment variable configuration for all settings
- Python API for programmatic video generation
- Async/await support for efficient processing
- Comprehensive error handling and retry logic
- Support for Python 3.11, 3.12, and 3.13

### Dependencies
- moviepy >= 2.0.0
- openai >= 1.12.0
- httpx >= 0.27.0
- pydantic >= 2.6.0
- pydantic-settings >= 2.2.0
- python-dotenv >= 1.0.1
- aiofiles >= 23.2.1
- tenacity >= 8.2.3
- rich >= 13.7.0
- typer >= 0.9.0
- pillow >= 10.2.0
- numpy >= 1.26.0
- pyyaml >= 6.0.0

[Unreleased]: https://github.com/youhanasheriff/video-composer/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/youhanasheriff/video-composer/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/youhanasheriff/video-composer/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/youhanasheriff/video-composer/releases/tag/v0.2.0
[0.1.0]: https://github.com/youhanasheriff/video-composer/releases/tag/v0.1.0
