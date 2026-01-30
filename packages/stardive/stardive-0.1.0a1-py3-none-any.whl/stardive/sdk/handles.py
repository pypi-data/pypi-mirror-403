"""
ArtifactHandle - First-Class Artifact References for SDK.

This module provides the ArtifactHandle class, which enables type-safe,
mechanically traceable artifact references in the Stardive SDK.

Key Design Decisions:
1. **First-Class Handles**: Artifacts are NOT referenced by string IDs alone
2. **Type Safety**: IDE autocomplete works, multi-file workflows safe
3. **Mechanically Traceable**: Producer step and artifact name are explicit
4. **Unique Identity**: Internal UUID ensures uniqueness even with same step/name

Why First-Class Handles?

String-based dependencies (e.g., depends_on=["raw_data"]) have problems:
- **Ambiguity**: Which step produced "raw_data"?
- **No IDE support**: Typos not caught until runtime
- **Multi-file workflows**: Name collisions between files
- **Unclear lineage**: Can't trace data causality mechanically

ArtifactHandle solves these problems by making artifact references explicit:
- Handle knows WHICH step produced the artifact (producer_step_id)
- Handle knows the artifact's NAME (artifact_name)
- Handle has a UNIQUE ID (internal_id) for disambiguation
- IDE autocomplete works (handles are Python objects)
- Multi-file safe (handles carry full context)

Design Rationale:

This design follows the principle of "data causality over execution order":
- Dependencies are declared via artifact flow (what consumes what)
- Lineage becomes mechanically derivable (no guessing)
- Replay semantics become meaningful (trace exact data path)

Examples:
    Creating artifact handles:
        from stardive.sdk import ArtifactHandle

        # Create handles for artifacts a step will produce
        raw_data = ArtifactHandle(
            producer_step_id="fetch_data",
            artifact_name="raw_data"
        )

        analysis = ArtifactHandle(
            producer_step_id="analyze",
            artifact_name="analysis_result"
        )

    Using handles in step declarations:
        @ctx.step_meta(
            step_id="analyze",
            consumes=[raw_data],  # Type-safe reference
            produces=[analysis]
        )
        def analyze_data(data):
            return {"result": sum(data)}

    Multi-file workflows (handles carry context):
        # file1.py
        from stardive.sdk import ArtifactHandle
        raw_data = ArtifactHandle("fetch_data", "raw_data")

        # file2.py
        from file1 import raw_data  # Clear dependency
        @ctx.step_meta(consumes=[raw_data], ...)
        def process(data):
            pass

For detailed specifications, see:
- CURRENT_JOB.md (Phase 3.4 - Python SDK Core)
- CLAUDE.md (First-class handles principle)
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4


class ArtifactHandle:
    """
    First-class artifact reference for type-safe dependency declarations.

    ArtifactHandle represents a reference to an artifact that will be produced
    by a step during execution. It is NOT the artifact content itself, but a
    handle that can be used to declare dependencies in the SDK.

    Purpose:
        ArtifactHandle enables mechanically traceable lineage by making artifact
        references explicit. Instead of string-based dependencies (which are
        ambiguous), handles carry full context:
        - Which step produces this artifact (producer_step_id)
        - What the artifact is named (artifact_name)
        - A unique identifier for disambiguation (internal_id)

    Lifecycle:
        1. Create handle: `raw_data = ArtifactHandle("fetch", "raw_data")`
        2. Declare in step: `@ctx.step_meta(produces=[raw_data])`
        3. Reference in consuming step: `@ctx.step_meta(consumes=[raw_data])`
        4. Compile to RunPlan: `plan = ctx.compile()`
        5. Execute: Instrumentation API resolves handles to ArtifactRef

    Attributes:
        producer_step_id (str): Step ID that will produce this artifact
        artifact_name (str): Name of the artifact within the step
        internal_id (str): Unique UUID for disambiguation (private)

    Type Safety:
        ArtifactHandle is a Python object, so:
        - IDEs provide autocomplete (handles are real Python objects)
        - Type checkers validate usage (mypy/pyright detect errors)
        - Refactoring tools work (rename handles safely)

    Uniqueness:
        Even if two handles have the same producer_step_id and artifact_name,
        they are distinct objects with different internal_ids. This prevents
        accidental aliasing and ensures clear lineage.

    String Conversion:
        For convenience, handles can be created from strings in step_meta:
        - `produces=["output"]` → `produces=[ArtifactHandle(step_id, "output")]`
        - This is SUGAR only, handles are still created internally

    Examples:
        Basic handle creation:
            >>> from stardive.sdk import ArtifactHandle
            >>> raw_data = ArtifactHandle("fetch_data", "raw_data")
            >>> print(raw_data.producer_step_id)
            'fetch_data'
            >>> print(raw_data.artifact_name)
            'raw_data'

        Using handles in SDK:
            >>> ctx = StardiveContext()
            >>> raw_data = ctx.artifact("fetch_data", "raw_data")
            >>> analysis = ctx.artifact("analyze", "result")
            >>>
            >>> @ctx.step_meta(
            ...     step_id="analyze",
            ...     consumes=[raw_data],
            ...     produces=[analysis]
            ... )
            ... def analyze(data):
            ...     return {"result": sum(data)}

        Multi-file workflows:
            # shared_artifacts.py
            >>> from stardive.sdk import ArtifactHandle
            >>> SHARED_DATA = ArtifactHandle("loader", "shared_data")

            # workflow.py
            >>> from shared_artifacts import SHARED_DATA
            >>> @ctx.step_meta(consumes=[SHARED_DATA], ...)
            ... def process(data):
            ...     pass

        Handle equality (by internal_id):
            >>> handle1 = ArtifactHandle("step1", "output")
            >>> handle2 = ArtifactHandle("step1", "output")
            >>> handle1 == handle2  # Different internal_ids
            False
            >>> handle1 == handle1  # Same object
            True

        Hash for use in sets/dicts:
            >>> handles = {raw_data, analysis}
            >>> raw_data in handles
            True

    See Also:
        - StardiveContext.artifact(): Factory method for creating handles
        - StepSpec: Uses handles for consumes/produces declarations
        - ArtifactRef: Runtime reference to actual artifact content
    """

    def __init__(
        self,
        producer_step_id: str,
        artifact_name: str,
        internal_id: Optional[str] = None,
    ):
        """
        Initialize an ArtifactHandle.

        Args:
            producer_step_id: Step ID that will produce this artifact
            artifact_name: Name of the artifact within the step
            internal_id: Internal UUID (auto-generated if not provided)

        Raises:
            ValueError: If producer_step_id or artifact_name is empty

        Note:
            Most users should create handles via `ctx.artifact()` instead of
            calling this constructor directly.
        """
        if not producer_step_id or not producer_step_id.strip():
            raise ValueError("producer_step_id cannot be empty")
        if not artifact_name or not artifact_name.strip():
            raise ValueError("artifact_name cannot be empty")

        self._producer_step_id = producer_step_id.strip()
        self._artifact_name = artifact_name.strip()
        self._internal_id = internal_id or f"ah_{uuid4().hex[:16]}"

    @property
    def producer_step_id(self) -> str:
        """Step ID that will produce this artifact."""
        return self._producer_step_id

    @property
    def artifact_name(self) -> str:
        """Name of the artifact within the step."""
        return self._artifact_name

    @property
    def internal_id(self) -> str:
        """
        Unique internal identifier for this handle.

        This is used to distinguish between different handle instances even
        if they have the same producer_step_id and artifact_name. It ensures
        that handles are unique objects with clear identity.

        Note:
            This is an internal implementation detail. Users should not rely
            on the specific format of this ID.
        """
        return self._internal_id

    def __repr__(self) -> str:
        """Human-readable representation for debugging."""
        return (
            f"ArtifactHandle("
            f"producer_step_id={self.producer_step_id!r}, "
            f"artifact_name={self.artifact_name!r}, "
            f"internal_id={self.internal_id!r})"
        )

    def __str__(self) -> str:
        """String representation for display."""
        return f"{self.producer_step_id}.{self.artifact_name}"

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison based on internal_id.

        Two handles are equal ONLY if they have the same internal_id.
        This ensures that even handles with identical producer_step_id
        and artifact_name are distinct objects unless they're the same handle.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is an ArtifactHandle with same internal_id
        """
        if not isinstance(other, ArtifactHandle):
            return NotImplemented
        return self.internal_id == other.internal_id

    def __hash__(self) -> int:
        """
        Hash based on internal_id (for use in sets/dicts).

        This enables ArtifactHandles to be used as dictionary keys or
        stored in sets, which is useful for dependency tracking.

        Returns:
            int: Hash of internal_id
        """
        return hash(self.internal_id)

    def to_dict(self) -> dict:
        """
        Convert handle to dictionary for serialization.

        This is useful when compiling to RunPlan, where handles need to be
        converted to ArtifactSpec objects.

        Returns:
            dict: Dictionary with producer_step_id, artifact_name, internal_id

        Examples:
            >>> handle = ArtifactHandle("step1", "output")
            >>> handle.to_dict()
            {
                'producer_step_id': 'step1',
                'artifact_name': 'output',
                'internal_id': 'ah_...'
            }
        """
        return {
            "producer_step_id": self.producer_step_id,
            "artifact_name": self.artifact_name,
            "internal_id": self.internal_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ArtifactHandle:
        """
        Create handle from dictionary (deserialization).

        This is useful when loading handles from stored RunPlans or other
        serialized representations.

        Args:
            data: Dictionary with producer_step_id, artifact_name, internal_id

        Returns:
            ArtifactHandle: Reconstructed handle

        Raises:
            KeyError: If required fields are missing

        Examples:
            >>> data = {
            ...     'producer_step_id': 'step1',
            ...     'artifact_name': 'output',
            ...     'internal_id': 'ah_1234567890abcdef'
            ... }
            >>> handle = ArtifactHandle.from_dict(data)
            >>> handle.producer_step_id
            'step1'
        """
        return cls(
            producer_step_id=data["producer_step_id"],
            artifact_name=data["artifact_name"],
            internal_id=data["internal_id"],
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ArtifactHandle",
]
