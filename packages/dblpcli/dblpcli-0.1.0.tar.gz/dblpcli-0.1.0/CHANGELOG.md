# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-23

Initial release of dblpcli - a CLI tool for interacting with the DBLP computer science bibliography.

### Added

#### Core Infrastructure
- Project setup with modern Python packaging (pyproject.toml, hatchling)
- DBLP API client with connection pooling via httpx
- Retry logic with exponential backoff and jitter for resilience
- Configurable timeout and max retries via environment variables (`DBLP_TIMEOUT`, `DBLP_MAX_RETRIES`)

#### Output Formats
- Explicit `--format` / `-f` flag for output format selection
- Table format using Rich for human-readable terminal output
- JSON format for agent/script consumption
- BibTeX format fetched directly from DBLP (not generated)

#### Publication Commands
- `search` - Search publications with boolean query support (AND/OR operators)
- `pub` - Get publication details by DBLP key
- `bibtex` - Export BibTeX for single or multiple publications
  - Batch operations for multiple keys
  - Custom citation key support (`--key`)
  - Direct file output (`--output`)

#### Author Commands
- `author search` - Search authors by name
- `author get` - Get author details by persistent identifier (PID)
- `author pubs` - List author's publications with year filtering
- `author bibtex` - Export all author publications as BibTeX

#### Venue Commands
- `venue search` - Search venues (conferences/journals) with type filtering
- `venue get` - Get venue details and metadata
- `venue pubs` - List publications from a venue with year filtering

#### Filtering & Pagination
- Year filtering with range support (`--year 2020-2024`)
- Result limiting (`--limit`)
- Pagination offset (`--offset`)
- Venue type filtering (`--type conf/journals`)

#### Error Handling
- Structured error responses for both human and agent consumption
- Helpful suggestions on errors (e.g., "Try searching with...")
- Graceful handling of network errors, rate limits, and not-found responses

#### Testing & CI/CD
- Unit tests for API client and XML parsing
- Integration tests for CLI commands with mocked HTTP responses
- End-to-end tests against real DBLP API
- GitHub Actions CI workflow (Python 3.10-3.13)
- GitHub Actions publish workflow for PyPI releases

#### Documentation
- README with installation and usage examples
- Comprehensive PLAN.md with architecture documentation
- Command help text and docstrings throughout

[Unreleased]: https://github.com/mrshu/dblpcli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mrshu/dblpcli/releases/tag/v0.1.0
