"""
Stardive - Audit-Grade Execution Truth Layer for AI Workflows

Stardive exists to make AI execution provable — not smarter, faster, or more automated.

Core Principle: Observation and provenance, not control. We capture truth, we don't orchestrate.

Value = Lineage + Replay + Artifact Truth

Usage:
    # v0.1 MVP: SDK and Instrumentation (Coming Soon)

    # Python SDK (Context-scoped, metadata-only)
    from stardive import StardiveContext

    ctx = StardiveContext()

    @ctx.step_meta(step_id="fetch", produces=["data"], depends_on=[])
    def fetch_data():
        return {"data": [1, 2, 3]}

    plan = ctx.compile(initiator={"user": "alice"})

    # Instrumentation API (Zero-replacement adoption)
    from stardive.instrumentation import emit_run_start, emit_step_start, emit_step_end

    run_id = emit_run_start(initiator={"user": "bob"})
    emit_step_start(run_id, step_id="process", inputs={"data": [1, 2, 3]})
    result = your_function(data)
    emit_step_end(run_id, step_id="process", outputs={"result": result})

For more information, visit: https://stardive.xyz
"""

__version__ = "0.1.0a1"
__author__ = "Stardive Contributors"
__license__ = "AGPL-3.0-or-later"

# Phase 0-2 Complete: Core models available
from stardive.models import (
    RunPlan,
    RunRecord,
    RunPlanBuilder,
    RunRecordBuilder,
)

# SDK (Phase 3+ now available)
from stardive.sdk import StardiveContext

from stardive.instrumentation import (
    emit_run_start,
    emit_step_start,
    emit_artifact,
    emit_step_end,
    emit_run_end,
)

__all__ = [
    "__version__",
    # Core models (Phase 0-2 Complete)
    "RunPlan",
    "RunRecord",
    "RunPlanBuilder",
    "RunRecordBuilder",
    # SDK
    "StardiveContext",
    # Instrumentation
    "emit_run_start",
    "emit_step_start",
    "emit_artifact",
    "emit_step_end",
    "emit_run_end",
]
