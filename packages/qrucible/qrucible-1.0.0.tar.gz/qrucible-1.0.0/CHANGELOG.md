# Changelog

All notable changes to this project are documented here. This follows [Keep a Changelog](https://keepachangelog.com/) format and [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-01-24

**First stable release!**

This release marks Qrucible as production-ready. Starting with v1.0.0, the public API is considered stable and we follow semantic versioning.

### Added
- **OHLC Data Validation**: Comprehensive validation for bar data including:
  - Price positivity checks (open, high, low, close must be > 0)
  - OHLC consistency checks (high >= low, high >= open/close, low <= open/close)
  - Volume non-negativity checks
  - Timestamp ordering validation
  - Finite value checks (no NaN or Inf)
- **Minimum Data Validation**: Clear error messages when insufficient data is provided for indicator warm-up periods
- **Comprehensive Test Suite**: 50+ new tests covering:
  - All 20+ strategy types
  - Edge cases (empty data, invalid configs)
  - Data validation
  - Advanced order types (trailing stops, break-even, pyramiding)
  - External signals mode
  - Result consistency
  - Grid search functionality
- **API Stability Guarantee**: Public API is now stable; breaking changes will only occur in major versions

### Changed
- **Error Handling**: Replaced unsafe `unwrap()` calls with proper error handling using `Option::map()` and `unwrap_or()` patterns
- **Development Status**: Updated from "Beta" to "Production/Stable" in package classifiers
- **Version**: Bumped from 0.1.0 to 1.0.0

### Fixed
- ATR-based stops now gracefully fall back to percentage-based stops when ATR is unavailable
- Trailing stop calculations handle missing ATR values without panicking

## [0.1.0] - 2024-01-14

### Added
- Tag-triggered PyPI release workflow (wheels for Linux/macOS/Windows, sdist, trusted publishing)
- Documentation site scaffold with mkdocs-material and GitHub Pages deploy workflow
- Issue/PR templates and contributing guide for new contributors
- Benchmark script now prints copy-pasteable Markdown tables with environment details
- Real-data demo script using a public Apple OHLCV sample
- Initial public preview of Qrucible: Rust hot path with Python bindings for backtesting

### Changed
- README badges, docs link, and install notes to match packaging behavior
- Standardized project licensing to Apache-2.0 across Rust and Python metadata
