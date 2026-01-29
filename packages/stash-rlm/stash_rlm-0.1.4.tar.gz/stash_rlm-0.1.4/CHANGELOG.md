# Changelog

## [0.1.4] - 2026-01-24
### Added
- `ctx-rm` context removal command

## [0.1.3] - 2026-01-24
### Added
- `version` subcommand
- `export` / `import` JSON commands
- `ctx-list` / `ctx-info` context helpers

## [0.1.2] - 2026-01-24
### Added
- `--version` flag in CLI
- GitHub Actions CI (basic CLI smoke test)
- Repository metadata: CONTRIBUTING, CODE_OF_CONDUCT, SECURITY
- README badges

## [0.1.1] - 2026-01-24
### Fixed
- Validation for chunk size/overlap
- Graceful handling of invalid regex/FTS queries
- Avoid access-count updates during search
- Remove context search limit
- Safer memory key generation

## [0.1.0] - 2026-01-24
### Added
- Initial release
- SQLite-backed storage, FTS search
- Context loading, peek, chunk, remember/recall
