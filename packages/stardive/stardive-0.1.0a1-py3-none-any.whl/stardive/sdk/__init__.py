"""
Stardive SDK - Code-based workflow definition.

This module provides Python SDK for defining workflows using:
- StardiveContext: Context-scoped step registration with first-class handles
- ArtifactHandle: Type-safe artifact references for consumes/produces
- @ctx.step_meta(): Decorator for step registration

All patterns compile to the same canonical RunPlan.

Quick Start:

    Context Pattern (Recommended):
        from stardive.sdk import StardiveContext

        ctx = StardiveContext()

        # Create first-class artifact handles
        raw_data = ctx.artifact("fetch", "raw_data")
        result = ctx.artifact("analyze", "result")

        @ctx.step_meta("fetch", produces=[raw_data])
        def fetch_data():
            return {"data": [1, 2, 3]}

        @ctx.step_meta("analyze", consumes=[raw_data], produces=[result])
        def analyze(data):
            return {"sum": sum(data["data"])}

        plan = ctx.compile(initiator={"user": "alice"})

    Multi-file Workflows:
        # shared.py
        from stardive.sdk import StardiveContext
        ctx = StardiveContext()
        shared_data = ctx.artifact("loader", "data")

        # loader.py
        from shared import ctx, shared_data

        @ctx.step_meta("loader", produces=[shared_data])
        def load():
            return {"items": [...]}

        # processor.py
        from shared import ctx, shared_data

        @ctx.step_meta("process", consumes=[shared_data])
        def process(data):
            return transform(data)

For documentation, see: docs/sdk-guide.md
"""

# Import core SDK components
from .handles import ArtifactHandle
from .context import (
    StardiveContext,
    ContextRegisteredStep,
    StepIdCollisionError,
    ArtifactNotProducedError,
    ProducerStepNotFoundError,
    CycleDetectedError,
)

# Import legacy models (for backwards compatibility)
from .models import RegisteredStep
from .registry import StepRegistry

__all__ = [
    # Primary SDK interface
    "StardiveContext",
    "ArtifactHandle",
    # Context types and errors
    "ContextRegisteredStep",
    "StepIdCollisionError",
    "ArtifactNotProducedError",
    "ProducerStepNotFoundError",
    "CycleDetectedError",
    # Legacy (for backwards compatibility)
    "RegisteredStep",
    "StepRegistry",
]

__version__ = "0.1.0a1"
