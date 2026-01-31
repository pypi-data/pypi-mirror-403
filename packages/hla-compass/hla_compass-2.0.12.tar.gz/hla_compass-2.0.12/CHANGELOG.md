# Changelog

All notable changes to the HLA-Compass SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--sdk-path` / `HLA_COMPASS_SDK_PATH` to build/dev/serve/test/publish for local SDK validation.
- `--platform` to build/publish for explicit architecture targeting (multi-arch via buildx + `--push`).

### Removed
- Interactive module wizard + generator.
- Local dev server (`dev_server`) and mock testing utilities (`ModuleTester`, `MockContext`).
- CLI commands: `completions`, `config`, `data`, `list`, and legacy auth aliases.
- MCP descriptor generation during `build`.
- Async API client (`AsyncAPIClient`) and `httpx` dependency.
- `Module.serve` helper and runner serve-mode (`HLA_COMPASS_RUN_MODE=serve`).

### Changed
- `hla-compass test` now runs containerized tests by default.
- UI template dev flow uses `hla-compass serve` + webpack proxy for `/api`.

### Fixed
- N/A

## [2.0.0] - 2024-11-XX

### Added
- `DataClient` with scoped SQL and Storage access
- `ModuleTester.quickstart()` for rapid testing
- Pydantic `Input` model support for typed inputs
- `hla-compass preflight` command for manifest sync
- Storage helpers: `save_json`, `save_csv`, `save_excel`

### Changed
- Module execution now uses `RuntimeContext` with typed properties
- Manifest schema auto-generated from Pydantic models

## [1.0.0] - 2024-XX-XX

- Initial public release
