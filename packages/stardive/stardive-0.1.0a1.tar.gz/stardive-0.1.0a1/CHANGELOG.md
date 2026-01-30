# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0a1] - 2026-01-26

### Added

#### Core Infrastructure
- **Canonical IR (Internal Representation)**: RunPlan and RunRecord models for execution intent and audit truth
- **Identity & Provenance System**: Comprehensive tracking of who/where/with-what
  - Identity models (human, service, system)
  - EnvironmentFingerprint for reproducibility
  - ModelIdentity and ToolIdentity for AI governance
  - ApprovalAttestation and NonDeterminismAttestation
- **Append-Only Storage Backend**: SQLite with tamper-evident guarantees
  - Event storage with hash chains
  - Artifact storage with hybrid inline/file strategy
  - Database triggers preventing retroactive modifications
- **Artifact Management**: Complete artifact lifecycle with canonicalization
  - Deterministic JSON serialization with SHA256 hashing
  - Support for JSON, TEXT, BYTES, and FILE kinds
- **Secret Detection & Redaction**: Multi-layered protection against secret leakage
  - Best-effort and strict modes
  - Redaction policies for secure storage
- **Execution Kernel**: Full workflow execution engine
  - Step-by-step execution with event emission
  - Context management and error handling
- **Lineage & Verification**: Audit trail construction and validation
  - Lineage graph construction
  - Hash chain integrity verification
- **Replay Engine**: Execution replay with verification
- **SDK**: Multiple integration modes (decorators, context managers, explicit API)

#### Testing
- **648 comprehensive tests** with 94% overall coverage
- Security tests for secret detection and redaction

### Fixed
- SQL injection vulnerability in `list_runs()` LIMIT/OFFSET (changed to parameterized queries)

### Security
- Parameterized SQL queries throughout (SQL injection prevention)
- Secret detection with strict mode
- Append-only storage with tamper-evident guarantees
- Hash chain integrity for audit trails

### Known Limitations
- SQLite backend only (PostgreSQL planned for v0.2.0)
- File system artifact storage only (S3 planned for v0.2.0)
- Basic replay functionality (advanced replay planned for v0.2.0)

---

[Unreleased]: https://github.com/StarDiveAI/stardive-core/compare/v0.1.0a1...HEAD
[0.1.0a1]: https://github.com/StarDiveAI/stardive-core/releases/tag/v0.1.0a1
