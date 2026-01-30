# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-25

### Added
- Created `CHANGELOG.md` to track project changes.

### Changed
- **Performance Optimization**: Transitioned from using Polars Series for distribution parameters (`mean`, `std`) to typed Rust `kwargs`. This significantly reduces overhead for scalar parameters.
- **Improved Rust Implementation**: Switched to `apply_values` for `normal_cdf` and `normal_pdf`, improving performance by avoiding `Option` wrapping for non-null values.
- **Python API Refinement**: Updated `normal_cdf`, `normal_ppf`, and `normal_pdf` to accept scalar floats for `mean` and `std` and pass them via `kwargs`. Added early validation in Python.
- Updated `README.md` to reflect the optimized API.

### Fixed
- Fixed a bug in the benchmark script where results were not being returned.

## [0.1.0] - 2026-01-25

### Added
- Initial release with `normal_cdf`, `normal_ppf`, and `normal_pdf` functions.
- Rust-based Polars plugin implementation using `statrs`.
- Python wrapper for easy integration with Polars expressions.
- Basic test suite and benchmarks.
