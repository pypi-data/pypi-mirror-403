# Changelog

All notable changes to GridSeal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-30

### Added

- **Citation Check**: NLI-based claim verification using cross-encoder models
- **LangChain Integration**: `GridSealCallbackHandler` for seamless LangChain support
- Optional `[nli]` and `[langchain]` dependency groups

### Changed

- Updated verification checks `__init__.py` to export CitationCheck
- Engine now supports citation check in CHECK_REGISTRY

## [0.2.0] - 2026-01-30

### Added

- **Confidence Check**: Embedding-based coherence and consistency scoring
- **Relevance Check**: Query-response relevance measurement
- **PostgreSQL Backend**: Enterprise-grade persistent storage with ACID compliance
- CLI `init` command for database initialization
- Enhanced `stats` command with pass rate calculation

### Changed

- Verification engine supports multiple check types
- AuditStore supports PostgreSQL via `psycopg2`

## [0.1.0] - 2026-01-30

### Added

- **Core Types**: `CheckResult`, `VerificationResult`, `AuditRecord`
- **Configuration**: Pydantic-based config with `VerificationConfig`, `AuditConfig`, `GridSealConfig`
- **Grounding Check**: Embedding-based hallucination detection using sentence-transformers
- **Verification Engine**: Orchestrates multiple checks with configurable thresholds
- **Audit Store**: Immutable logging with hash-chain integrity
- **SQLite Backend**: Production-ready persistent storage
- **Memory Backend**: In-memory storage for testing
- **Langfuse Adapter**: Integration with Langfuse observability platform
- **CLI**: Basic commands (`version`, `verify`, `export`, `stats`)
- **Decorators**: `@gs.verify` and `@gs.audit` for function wrapping
- Comprehensive test suite with 205 tests and 90%+ coverage

### Security

- Hash-chain integrity verification for audit records
- Tamper-evident logging with SHA-256 checksums
