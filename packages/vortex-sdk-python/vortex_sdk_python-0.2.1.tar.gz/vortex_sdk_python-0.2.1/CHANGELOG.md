# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-01-23

### Changed
- Updated to Vortex SDK 0.5.1

## [0.2.0] - 2026-01-23

### Changed
- Updated to latest Vortex SDK

## [0.1.0] - 2025-11-04

### Added
- Initial release of vortex-sdk-python
- Python wrapper for Vortex SDK using Node.js subprocess execution
- Support for both local and globally installed `@vortexfi/sdk` npm package
- Full type hints and py.typed support
- Synchronous and asynchronous API methods
- Support for BRL on-ramp and off-ramp operations
- PIX payment integration
- Complete example scripts demonstrating usage
- Comprehensive documentation and installation guides

### Changed
- Removed PythonMonkey dependency in favor of Node.js subprocess approach
- Updated all documentation to reflect new architecture

### Fixed
- Module import errors when using globally installed npm packages

### Added
- Initial development version (not published)

[Unreleased]: https://github.com/pendulum-chain/vortex-python-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pendulum-chain/vortex-python-sdk/releases/tag/v0.1.0
