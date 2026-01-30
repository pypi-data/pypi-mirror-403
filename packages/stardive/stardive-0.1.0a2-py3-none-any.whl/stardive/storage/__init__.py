"""
Storage Layer for Stardive - Append-Only Truth Kernel.

This module provides the storage backend interface and implementations for
Stardive's audit-grade execution truth layer.

Public API:
    - StorageBackend: Abstract interface for storage backends
    - VerificationReport: Result of integrity verification
    - NamespaceFilter: Filters for querying runs

Available Backends:
    - SQLiteBackend: SQLite-based storage

Example Usage:
    from stardive.storage import SQLiteBackend, VerificationReport
    from stardive.models import RunStartEvent, Identity

    # Create backend
    backend = SQLiteBackend(db_path="stardive.db")

    # Store event
    backend.store_event(
        RunStartEvent(
            run_id="run_abc123",
            plan_ref="run_abc123",
            initiator=Identity(...),
            event_hash="sha256:...",
            previous_hash=None
        )
    )

    # Verify integrity
    report = backend.verify_run("run_abc123")
    if report.verified:
        print("Run is valid and untampered")
"""

from .base import (
    StorageBackend,
    VerificationReport,
    NamespaceFilter,
)
from .sqlite import SQLiteBackend

__all__ = [
    "StorageBackend",
    "VerificationReport",
    "NamespaceFilter",
    "SQLiteBackend",
]
