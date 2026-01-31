# Changelog

All notable changes to srx-lib-llm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.13.1] - 2025-12-10

### Fixed
- Fixed `extract_structured()` to accept `reasoning_effort` parameter
- Added automatic model detection: GPT-5.* models now use `extract_structured_gpt51()` with reasoning_effort support
- Default reasoning_effort to "low" for GPT-5.* models when not specified
- Non-GPT-5.* models (e.g., gpt-4.1-mini) ignore reasoning_effort parameter (backward compatible)

## [1.13.0] - 2025-12-10

### Changed
- Updated `extract_structured_gpt51()` default model from `gpt-5.1` to `gpt-5.1-2025-11-13` snapshot
- Updated `extract_structured_gpt51()` default reasoning_effort from `none` to `medium`
- Added GPT-5.1 snapshot versions to `MODELS_SUPPORTING_NONE_REASONING` set for better model detection

### Added
- Support for GPT-5.1 snapshot versions: `gpt-5.1-2025-11-13`, `gpt-5.1-chat-2025-11-13`, `gpt-5.1-codex-2025-11-13`
- Documentation for GPT-5.1 with medium reasoning effort use cases
- Usage examples for complex analysis tasks with GPT-5.1

### Documentation
- Added GPT-5.1 with medium reasoning profile to GPT_MODEL_HYPERPARAMETERS_GUIDE.md
- Added GPT-5.1 usage example to README.md
- Documented cost-benefit trade-offs for medium reasoning effort

## [1.12.0] - Previous Release

Initial stable release with GPT-5 support, structured output helpers, and OpenAI Batch API wrapper.
