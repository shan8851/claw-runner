# Changelog

All notable changes to this project will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-01-31

### Added

- Community-focused README
- Basic URL scheme allowlist (`http`, `https`, `file`) when opening links
- Package `__version__`

### Changed

- Simplified config loading with clearer defaults and type checks
- Use `Path.as_uri()` when opening files to handle spaces safely

(When tagging releases, use tags like `v0.1.0`.)
