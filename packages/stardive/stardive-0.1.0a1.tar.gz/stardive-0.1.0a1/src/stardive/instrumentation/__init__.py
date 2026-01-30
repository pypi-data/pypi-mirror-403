"""
Instrumentation API for Zero-Replacement Adoption of Stardive.

This module provides the core instrumentation API that enables users to wrap
existing AI workflows with minimal code changes (~10-20 lines) to obtain
audit-grade execution records.

Key Design Principles:
1. **Zero-Replacement**: Wrap existing code, don't replace it
2. **Explicit Context**: No thread-local magic, explicit RunContext passing
3. **Explicit Artifacts**: Only JSON-serializable content via emit_artifact()
4. **Immediate Storage**: Events stored immediately for audit integrity
5. **Type-Safe**: Accept ArtifactRef objects, not arbitrary Python objects

Core Components:
- **RunContext**: Container for run_id, builder, and storage backend
- **emit_run_start()**: Initialize execution tracking
- **emit_step_start()**: Mark step beginning with typed inputs
- **emit_artifact()**: Explicitly capture and hash artifacts
- **emit_step_end()**: Mark step completion with typed outputs

Usage Pattern:
    ```python
    from stardive.instrumentation import (
        emit_run_start, emit_step_start, emit_artifact, emit_step_end
    )
    from stardive.storage import SQLiteBackend
    from stardive.artifacts import ArtifactKind

    # Initialize storage
    storage = SQLiteBackend(db_path="audit.db")

    # Start tracking execution
    run_ctx = emit_run_start(
        storage=storage,
        initiator={"user": "alice", "auth_method": "sso"}
    )

    # Wrap existing workflow
    emit_step_start(run_ctx, step_id="process")

    # Your existing code (unchanged)
    result = your_function(data)

    # Explicitly capture artifact
    artifact = emit_artifact(
        run_ctx,
        step_id="process",
        name="result",
        content={"prediction": result},
        kind=ArtifactKind.JSON
    )

    # Mark completion
    emit_step_end(
        run_ctx,
        step_id="process",
        outputs={"result": artifact}
    )
    ```

Why Instrumentation API?
    The instrumentation API is the CRITICAL PATH for Stardive adoption because:

    1. **Zero Replacement**: Users don't need to rewrite existing workflows
    2. **Framework Agnostic**: Works with LangChain, notebooks, batch jobs
    3. **Incremental Adoption**: Add tracking gradually, step by step
    4. **Immediate Value**: Audit trails without orchestration changes

For detailed specifications, see:
- docs/instrumentation-guide.md (to be created)
- CURRENT_JOB.md (Phase 3.3)
"""

from .context import RunContext
from .api import (
    emit_run_start,
    emit_step_start,
    emit_artifact,
    emit_step_end,
    emit_run_end,
)

__all__ = [
    "RunContext",
    "emit_run_start",
    "emit_step_start",
    "emit_artifact",
    "emit_step_end",
    "emit_run_end",
]
