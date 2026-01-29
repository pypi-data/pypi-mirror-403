# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-25

### Added

- Initial release of fs-box-sync Python SDK
- 3-layer architecture (BoxAPI, BoxDrive, BoxFS)
- Async-first API using httpx and aiofiles
- OAuth token management with persistent cross-platform storage
- Automatic token refresh with fallback to token provider
- File operations: upload, download, delete, move
- Chunked uploads for files >20MB with SHA1 hashing
- Folder operations: list, create, search
- Box Drive integration with sync verification
- Three sync strategies: poll, smart, force
- Webhook management (create, delete, list)
- Shared link file download support
- Cross-platform Box Drive path detection (Windows, macOS, Linux)
- Date-based folder structure creation with locale support
- Comprehensive exception hierarchy
- Full type hints with pyright strict mode
