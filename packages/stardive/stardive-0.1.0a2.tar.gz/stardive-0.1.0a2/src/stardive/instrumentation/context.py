"""
RunContext - Explicit Context Container for Instrumentation API.

This module provides the RunContext class, which is the central container
for all state needed during instrumentation-based execution tracking.

Key Design Decisions:
1. **Explicit Context Passing**: No thread-local magic, context passed explicitly
2. **Immutable After Creation**: RunContext is read-only after initialization
3. **Encapsulates Builder State**: Holds RunRecordBuilder for incremental construction
4. **Manages Storage**: References storage backend for immediate event persistence

Why Explicit Context?
    Thread-local state is convenient but causes problems:
    - Hard to test (implicit global state)
    - Breaks with async code (task switching)
    - Confusing in multi-run scenarios
    - Makes dependencies unclear

    Explicit context passing makes code easier to:
    - Test (inject mock contexts)
    - Debug (see what's being tracked)
    - Reason about (no hidden state)
    - Use safely (no global pollution)

Thread Safety:
    RunContext itself is immutable after creation, but the underlying
    RunRecordBuilder is NOT thread-safe. If multiple threads will emit
    events concurrently, external synchronization is required.

For detailed specifications, see:
- CURRENT_JOB.md (Phase 3.3 - Instrumentation API)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from stardive.models import RunRecordBuilder
from stardive.storage import StorageBackend


class RunContext:
    """
    Explicit context container for instrumentation-based execution tracking.

    RunContext holds all state needed to track a single run execution:
    - run_id: Unique identifier for this execution
    - builder: RunRecordBuilder for incremental event construction
    - storage: StorageBackend for immediate event persistence

    Purpose:
        RunContext provides explicit context passing for instrumentation APIs.
        Every emit_* function accepts a RunContext, making dependencies clear
        and avoiding thread-local state.

    Lifecycle:
        1. Create via emit_run_start()
        2. Pass to emit_step_start(), emit_artifact(), emit_step_end()
        3. Optionally pass to emit_run_end() for explicit completion
        4. Context remains valid until run completes

    Immutability:
        RunContext is immutable after creation (read-only properties).
        The underlying builder is mutable (for incremental construction),
        but the context reference itself doesn't change.

    Examples:
        Basic usage:
            storage = SQLiteBackend(db_path="audit.db")
            run_ctx = emit_run_start(storage=storage, initiator={...})

            # Pass context explicitly to all emit functions
            emit_step_start(run_ctx, step_id="process")
            artifact = emit_artifact(run_ctx, step_id="process", ...)
            emit_step_end(run_ctx, step_id="process", outputs={"result": artifact})

        Multiple concurrent runs (safe because explicit):
            run_ctx_1 = emit_run_start(storage=storage, initiator=user_1)
            run_ctx_2 = emit_run_start(storage=storage, initiator=user_2)

            # No confusion - each context tracks its own run
            emit_step_start(run_ctx_1, step_id="process")
            emit_step_start(run_ctx_2, step_id="process")

    Attributes:
        run_id (str): Unique identifier for this execution (UUID format)
        builder (RunRecordBuilder): Incremental builder for constructing RunRecord
        storage (StorageBackend): Storage backend for immediate event persistence
        start_time (datetime): When this run was initiated (for duration calculation)
    """

    def __init__(
        self,
        run_id: str,
        builder: RunRecordBuilder,
        storage: StorageBackend,
        start_time: Optional[datetime] = None,
    ):
        """
        Initialize RunContext (typically called by emit_run_start()).

        Args:
            run_id: Unique identifier for this execution
            builder: RunRecordBuilder for incremental construction
            storage: StorageBackend for immediate event persistence
            start_time: When this run was initiated (defaults to now)

        Note:
            Users should typically create RunContext via emit_run_start()
            rather than calling this constructor directly.
        """
        self._run_id = run_id
        self._builder = builder
        self._storage = storage
        self._start_time = start_time or datetime.utcnow()

    @property
    def run_id(self) -> str:
        """Unique identifier for this execution."""
        return self._run_id

    @property
    def builder(self) -> RunRecordBuilder:
        """Incremental builder for constructing RunRecord."""
        return self._builder

    @property
    def storage(self) -> StorageBackend:
        """Storage backend for immediate event persistence."""
        return self._storage

    @property
    def start_time(self) -> datetime:
        """When this run was initiated."""
        return self._start_time

    def __repr__(self) -> str:
        """Human-readable representation for debugging."""
        return (
            f"RunContext(run_id={self.run_id!r}, "
            f"start_time={self.start_time.isoformat()}, "
            f"storage={self.storage.__class__.__name__})"
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on run_id."""
        if not isinstance(other, RunContext):
            return NotImplemented
        return self.run_id == other.run_id

    def __hash__(self) -> int:
        """Hash based on run_id (for use in sets/dicts)."""
        return hash(self.run_id)
