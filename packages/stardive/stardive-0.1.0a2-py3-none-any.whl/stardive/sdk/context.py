"""
StardiveContext - Context-Scoped Workflow Definition.

This module provides the StardiveContext class, which is the primary interface
for defining workflows using the Stardive SDK. StardiveContext provides:

1. **Context-Scoped Step Registration**: No global registry, each context is isolated
2. **First-Class Artifact Handles**: Type-safe artifact references
3. **Step ID Collision Detection**: Catch duplicate step IDs at registration time
4. **Dependency Validation**: Validate consumes/produces relationships
5. **Compilation to RunPlan**: Convert registered steps to canonical IR

Design Principles:
1. **No Global State**: Each context is isolated (better for testing)
2. **Explicit Over Implicit**: User declares dependencies, we don't infer
3. **Plan ≠ Run**: Compilation is separate from execution
4. **First-Class Handles**: ArtifactHandles, not string-based dependencies
5. **Type Safety**: IDE autocomplete works, multi-file safe

Usage:
    from stardive.sdk import StardiveContext, ArtifactHandle

    # Create context-scoped registry
    ctx = StardiveContext()

    # Create first-class artifact handles
    raw_data = ctx.artifact("fetch_data", "raw_data")
    analysis = ctx.artifact("analyze", "result")

    # Register steps with consumes/produces (not depends_on)
    @ctx.step_meta(
        step_id="fetch_data",
        produces=[raw_data]
    )
    def fetch_data():
        return {"data": [1, 2, 3]}

    @ctx.step_meta(
        step_id="analyze",
        consumes=[raw_data],
        produces=[analysis]
    )
    def analyze(raw_data):
        return {"result": sum(raw_data["data"])}

    # Compile to RunPlan (no execution happens)
    plan = ctx.compile(initiator={"user": "alice"})

For detailed specifications, see:
- CURRENT_JOB.md (Phase 3.4 - Python SDK Core)
- CLAUDE.md (SDK design principles)
"""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from stardive.models import (
    Identity,
    EnvironmentFingerprint,
    RunPlan,
    StepSpec,
    ArtifactSpec,
    ArtifactType,
    SourceType,
    PolicySpec,
    RunPlanBuilder,
)

from .handles import ArtifactHandle


# ============================================================================
# Type Aliases
# ============================================================================

# Handles can be ArtifactHandle or string (sugar for step_id.artifact_name)
HandleOrStr = Union[ArtifactHandle, str]


# ============================================================================
# Registered Step Model (Enhanced with consumes/produces)
# ============================================================================


class ContextRegisteredStep:
    """
    Step registered with StardiveContext.

    This is an enhanced version of RegisteredStep that supports:
    - consumes: ArtifactHandles this step consumes (inputs)
    - produces: ArtifactHandles this step produces (outputs)

    This enables mechanically traceable lineage via artifact flow.
    """

    def __init__(
        self,
        step_id: str,
        function: Callable,
        step_type: str,
        consumes: List[ArtifactHandle],
        produces: List[ArtifactHandle],
        config: Dict[str, Any],
        source_ref: str,
        description: Optional[str] = None,
        max_retries: int = 0,
        retry_delay_seconds: float = 1.0,
        timeout_seconds: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Initialize a registered step.

        Args:
            step_id: Unique step identifier
            function: Python function to execute
            step_type: Type of step (python, llm, sql, http)
            consumes: ArtifactHandles this step consumes
            produces: ArtifactHandles this step produces
            config: Step-specific configuration
            source_ref: Source code location (file.py:line)
            description: Human-readable description
            max_retries: Number of retry attempts on failure
            retry_delay_seconds: Delay between retries
            timeout_seconds: Step execution timeout
            tags: Tags for categorization
        """
        self.step_id = step_id
        self.function = function
        self.step_type = step_type
        self.consumes = consumes
        self.produces = produces
        self.config = config
        self.source_ref = source_ref
        self.description = description
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.timeout_seconds = timeout_seconds
        self.tags = tags or []

    def __repr__(self) -> str:
        return (
            f"ContextRegisteredStep(step_id={self.step_id!r}, "
            f"consumes={len(self.consumes)}, produces={len(self.produces)})"
        )


# ============================================================================
# Validation Errors
# ============================================================================


class StepIdCollisionError(ValueError):
    """Raised when a step ID is registered twice."""

    def __init__(self, step_id: str, first_source: str, second_source: str):
        self.step_id = step_id
        self.first_source = first_source
        self.second_source = second_source
        super().__init__(
            f"Step ID '{step_id}' already registered. "
            f"First registered at {first_source}, "
            f"collision at {second_source}."
        )


class ArtifactNotProducedError(ValueError):
    """Raised when a step consumes an artifact that no step produces."""

    def __init__(self, step_id: str, artifact_handle: ArtifactHandle):
        self.step_id = step_id
        self.artifact_handle = artifact_handle
        super().__init__(
            f"Step '{step_id}' consumes artifact '{artifact_handle}' but no step "
            f"produces it. Expected producer: '{artifact_handle.producer_step_id}'."
        )


class ProducerStepNotFoundError(ValueError):
    """Raised when an artifact's producer step doesn't exist."""

    def __init__(self, artifact_handle: ArtifactHandle):
        self.artifact_handle = artifact_handle
        super().__init__(
            f"Artifact '{artifact_handle}' declares producer step "
            f"'{artifact_handle.producer_step_id}' but that step is not registered."
        )


class CycleDetectedError(ValueError):
    """Raised when a dependency cycle is detected."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Dependency cycle detected: {cycle_str}")


# ============================================================================
# StardiveContext
# ============================================================================


class StardiveContext:
    """
    Context-scoped workflow definition and compilation.

    StardiveContext is the primary interface for defining workflows using the
    Stardive SDK. It provides:

    1. **Scoped Step Registry**: Steps are registered to this context only
    2. **Artifact Handle Factory**: Create first-class handles via ctx.artifact()
    3. **Step Metadata Decorator**: @ctx.step_meta() for step registration
    4. **Dependency Validation**: Validates consumes/produces relationships
    5. **Compile to RunPlan**: ctx.compile() produces canonical IR

    Design Principles:
        - **No Global Registry**: Each context is isolated (thread-safe by design)
        - **Explicit Dependencies**: User declares via consumes/produces
        - **Plan ≠ Run**: Compilation is separate from execution
        - **Type Safety**: ArtifactHandles enable IDE autocomplete

    Thread Safety:
        StardiveContext is NOT thread-safe. Each thread should create its own
        context. This is intentional: global state causes subtle bugs.

    Lifecycle:
        1. Create context: `ctx = StardiveContext()`
        2. Create handles: `data = ctx.artifact("step1", "output")`
        3. Register steps: `@ctx.step_meta(...)`
        4. Compile: `plan = ctx.compile(initiator={...})`
        5. Execute: Use instrumentation API or reference executor

    Examples:
        Simple workflow:
            ctx = StardiveContext()

            raw = ctx.artifact("fetch", "raw_data")
            result = ctx.artifact("process", "result")

            @ctx.step_meta("fetch", produces=[raw])
            def fetch_data():
                return {"items": [1, 2, 3]}

            @ctx.step_meta("process", consumes=[raw], produces=[result])
            def process(data):
                return {"sum": sum(data["items"])}

            plan = ctx.compile(initiator={"user": "alice"})

        Multi-file workflow:
            # shared.py
            from stardive.sdk import StardiveContext
            ctx = StardiveContext()
            raw_data = ctx.artifact("loader", "raw")

            # loader.py
            from shared import ctx, raw_data

            @ctx.step_meta("loader", produces=[raw_data])
            def load():
                return {"data": [1, 2, 3]}

            # analyzer.py
            from shared import ctx, raw_data

            @ctx.step_meta("analyzer", consumes=[raw_data])
            def analyze(data):
                return sum(data["data"])
    """

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize a new StardiveContext.

        Args:
            name: Optional workflow name
            description: Optional workflow description
        """
        self._name = name
        self._description = description

        # Scoped step registry: step_id -> ContextRegisteredStep
        self._steps: Dict[str, ContextRegisteredStep] = {}

        # Artifact handle tracking: internal_id -> ArtifactHandle
        self._handles: Dict[str, ArtifactHandle] = {}

        # Track which handles are expected to be produced
        self._expected_produces: Dict[str, ArtifactHandle] = {}  # internal_id -> handle

        # Track source locations for collision detection
        self._step_sources: Dict[str, str] = {}  # step_id -> source_ref

    # ========================================================================
    # Artifact Handle Factory
    # ========================================================================

    def artifact(self, producer_step_id: str, artifact_name: str) -> ArtifactHandle:
        """
        Create a first-class artifact handle.

        Handles are used to declare consumes/produces relationships in step_meta.
        They provide type-safe, mechanically traceable dependencies.

        Args:
            producer_step_id: Step ID that will produce this artifact
            artifact_name: Name of the artifact within the step

        Returns:
            ArtifactHandle: First-class handle for use in consumes/produces

        Examples:
            raw_data = ctx.artifact("fetch_data", "raw_data")

            @ctx.step_meta("fetch_data", produces=[raw_data])
            def fetch():
                return {...}

            @ctx.step_meta("analyze", consumes=[raw_data])
            def analyze(data):
                return {...}

        Note:
            Handles created here are tracked by the context for validation
            during compile().
        """
        handle = ArtifactHandle(
            producer_step_id=producer_step_id,
            artifact_name=artifact_name,
        )
        # Track handle
        self._handles[handle.internal_id] = handle
        return handle

    # ========================================================================
    # Step Registration Decorator
    # ========================================================================

    def step_meta(
        self,
        step_id: str,
        *,
        consumes: Optional[List[HandleOrStr]] = None,
        produces: Optional[List[HandleOrStr]] = None,
        step_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        max_retries: int = 0,
        retry_delay_seconds: float = 1.0,
        timeout_seconds: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> Callable[[Callable], Callable]:
        """
        Decorator for registering a function as a workflow step.

        This decorator captures metadata about the step WITHOUT executing the
        function. Execution happens later via the instrumentation API.

        Args:
            step_id: Unique identifier for this step
            consumes: List of ArtifactHandles (or strings) this step consumes
            produces: List of ArtifactHandles (or strings) this step produces
            step_type: Type of step (python, llm, sql, http). Auto-inferred if None.
            config: Step-specific configuration
            description: Human-readable description
            max_retries: Number of retry attempts on failure
            retry_delay_seconds: Delay between retries
            timeout_seconds: Step execution timeout
            tags: Tags for categorization

        Returns:
            Decorated function (unchanged)

        Raises:
            StepIdCollisionError: If step_id is already registered

        Examples:
            Basic registration:
                @ctx.step_meta("analyze")
                def analyze_data(data):
                    return result

            With consumes/produces:
                raw = ctx.artifact("fetch", "raw")
                result = ctx.artifact("analyze", "result")

                @ctx.step_meta(
                    "analyze",
                    consumes=[raw],
                    produces=[result]
                )
                def analyze(data):
                    return {"result": process(data)}

            String sugar (auto-creates handles):
                @ctx.step_meta(
                    "process",
                    consumes=["fetch.raw_data"],  # Parsed to handle
                    produces=["output"]  # Becomes "process.output"
                )
                def process(data):
                    return transform(data)
        """
        # Normalize consumes/produces
        consumes = consumes or []
        produces = produces or []

        def decorator(func: Callable) -> Callable:
            # Capture source location for collision detection
            source_ref = self._capture_source_location()

            # Check for step ID collision
            if step_id in self._steps:
                raise StepIdCollisionError(
                    step_id=step_id,
                    first_source=self._step_sources[step_id],
                    second_source=source_ref,
                )

            # Normalize handles (convert strings to ArtifactHandle)
            normalized_consumes = self._normalize_handles(consumes, step_id, is_consume=True)
            normalized_produces = self._normalize_handles(produces, step_id, is_consume=False)

            # Track expected produces
            for handle in normalized_produces:
                self._expected_produces[handle.internal_id] = handle
                # Also track in handles registry
                if handle.internal_id not in self._handles:
                    self._handles[handle.internal_id] = handle

            # Infer step type if not provided
            actual_step_type = step_type or self._infer_step_type(func)

            # Create registered step
            registered = ContextRegisteredStep(
                step_id=step_id,
                function=func,
                step_type=actual_step_type,
                consumes=normalized_consumes,
                produces=normalized_produces,
                config=config or {},
                source_ref=source_ref,
                description=description,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                timeout_seconds=timeout_seconds,
                tags=tags,
            )

            # Register step
            self._steps[step_id] = registered
            self._step_sources[step_id] = source_ref

            # Return original function unchanged
            return func

        return decorator

    # ========================================================================
    # Compilation
    # ========================================================================

    def compile(
        self,
        initiator: Union[Identity, Dict[str, Any]],
        environment: Optional[EnvironmentFingerprint] = None,
        policy: Optional[PolicySpec] = None,
        version: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> RunPlan:
        """
        Compile registered steps into an immutable RunPlan.

        This method:
        1. Validates all consumes/produces relationships
        2. Detects dependency cycles
        3. Builds the dependency graph from artifact flow
        4. Creates immutable RunPlan

        Args:
            initiator: Who is initiating this run (Identity or dict)
            environment: Execution environment (auto-detected if None)
            policy: Execution policy (permissive by default)
            version: Workflow version
            run_id: Run identifier (auto-generated if None)

        Returns:
            Immutable RunPlan ready for execution

        Raises:
            ArtifactNotProducedError: If a consumed artifact has no producer
            ProducerStepNotFoundError: If an artifact's producer step doesn't exist
            CycleDetectedError: If dependency graph has cycles

        Examples:
            Basic compile:
                plan = ctx.compile(initiator={"user": "alice"})

            With environment:
                plan = ctx.compile(
                    initiator=Identity(user_id="alice", ...),
                    environment=EnvironmentFingerprint(...),
                    version="1.0.0"
                )

        Note:
            Compilation does NOT execute the workflow. Use the instrumentation
            API or reference executor for execution.
        """
        from uuid import uuid4

        # Normalize initiator to Identity
        if isinstance(initiator, dict):
            initiator = self._dict_to_identity(initiator)

        # Auto-detect environment if not provided
        if environment is None:
            environment = self._detect_environment()

        # Generate run_id if not provided
        if run_id is None:
            run_id = f"run_{uuid4().hex[:16]}"

        # Validate dependencies
        self._validate_dependencies()

        # Build dependency graph from artifact flow
        dependencies = self._build_dependency_graph()

        # Create RunPlanBuilder
        builder = RunPlanBuilder(
            run_id=run_id,
            initiator=initiator,
            environment=environment,
            source_type=SourceType.SDK,
            source_ref=f"stardive.sdk.context:{self.__class__.__name__}",
            policy=policy or PolicySpec(),
            name=self._name,
            description=self._description,
            version=version,
        )

        # Add steps to builder
        for step_id, registered in self._steps.items():
            # Convert to StepSpec
            step_spec = StepSpec(
                step_id=step_id,
                step_type=registered.step_type,
                config=registered.config,
                executor_ref=self._get_executor_ref(registered.step_type),
                depends_on=dependencies.get(step_id, []),
                max_retries=registered.max_retries,
                retry_delay_seconds=registered.retry_delay_seconds,
                timeout_seconds=registered.timeout_seconds,
                description=registered.description,
                tags=registered.tags,
            )
            builder.add_step(step_spec)

        # Add expected artifacts
        for step_id, registered in self._steps.items():
            for handle in registered.produces:
                artifact_spec = ArtifactSpec(
                    artifact_id=handle.internal_id,
                    artifact_type=ArtifactType.OUTPUT,
                    produced_by_step=handle.producer_step_id,
                    name=handle.artifact_name,
                )
                builder.add_expected_artifact(artifact_spec)

        # Build immutable plan
        return builder.build()

    # ========================================================================
    # Validation
    # ========================================================================

    def _validate_dependencies(self) -> None:
        """
        Validate all consumes/produces relationships.

        Checks:
        1. Every consumed artifact has a producer step that's registered
        2. Producer step's produces list includes the artifact
        3. No dependency cycles

        Raises:
            ArtifactNotProducedError: If consumed artifact has no producer
            ProducerStepNotFoundError: If producer step doesn't exist
            CycleDetectedError: If cycles detected
        """
        # Check that all consumed artifacts are produced
        for step_id, registered in self._steps.items():
            for handle in registered.consumes:
                # Check producer step exists
                if handle.producer_step_id not in self._steps:
                    raise ProducerStepNotFoundError(handle)

                # Check producer step produces this artifact
                producer = self._steps[handle.producer_step_id]
                produced_ids = {h.internal_id for h in producer.produces}
                if handle.internal_id not in produced_ids:
                    # Handle might have been created separately - check by step/name
                    found = False
                    for prod_handle in producer.produces:
                        if (
                            prod_handle.producer_step_id == handle.producer_step_id
                            and prod_handle.artifact_name == handle.artifact_name
                        ):
                            found = True
                            break
                    if not found:
                        raise ArtifactNotProducedError(step_id, handle)

        # Check for cycles
        self._detect_cycles()

    def _detect_cycles(self) -> None:
        """
        Detect cycles in the dependency graph using DFS.

        Raises:
            CycleDetectedError: If a cycle is found
        """
        # Build adjacency list from artifact flow
        graph: Dict[str, Set[str]] = {step_id: set() for step_id in self._steps}

        for step_id, registered in self._steps.items():
            for handle in registered.consumes:
                # Edge: producer_step -> consumer_step
                if handle.producer_step_id in graph:
                    graph[handle.producer_step_id].add(step_id)

        # DFS for cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {v: WHITE for v in graph}
        parent: Dict[str, Optional[str]] = {v: None for v in graph}

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            color[node] = GRAY
            path.append(node)

            for neighbor in graph[node]:
                if color[neighbor] == GRAY:
                    # Found cycle - extract it from path
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
                elif color[neighbor] == WHITE:
                    result = dfs(neighbor, path)
                    if result:
                        return result

            color[node] = BLACK
            path.pop()
            return None

        for node in graph:
            if color[node] == WHITE:
                cycle = dfs(node, [])
                if cycle:
                    raise CycleDetectedError(cycle)

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build step dependency graph from artifact flow.

        Returns:
            Dict mapping step_id to list of step_ids it depends on
        """
        dependencies: Dict[str, List[str]] = {}

        for step_id, registered in self._steps.items():
            deps: List[str] = []
            for handle in registered.consumes:
                if handle.producer_step_id not in deps:
                    deps.append(handle.producer_step_id)
            dependencies[step_id] = deps

        return dependencies

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _normalize_handles(
        self,
        handles: List[HandleOrStr],
        current_step_id: str,
        is_consume: bool,
    ) -> List[ArtifactHandle]:
        """
        Normalize handles list to all ArtifactHandles.

        Strings are converted:
        - "step.artifact" -> ArtifactHandle(step, artifact)
        - "artifact" (for produces) -> ArtifactHandle(current_step_id, artifact)

        Args:
            handles: List of handles or strings
            current_step_id: Step ID for produces strings without step prefix
            is_consume: Whether this is for consumes (True) or produces (False)

        Returns:
            List of ArtifactHandles
        """
        result: List[ArtifactHandle] = []

        for h in handles:
            if isinstance(h, ArtifactHandle):
                result.append(h)
            elif isinstance(h, str):
                # Parse string format
                if "." in h:
                    # "step.artifact" format
                    parts = h.split(".", 1)
                    handle = ArtifactHandle(
                        producer_step_id=parts[0],
                        artifact_name=parts[1],
                    )
                else:
                    # "artifact" format - use current step for produces
                    if is_consume:
                        raise ValueError(
                            f"Consumed artifact '{h}' must specify producer step "
                            f"(use 'step_id.artifact_name' format)"
                        )
                    handle = ArtifactHandle(
                        producer_step_id=current_step_id,
                        artifact_name=h,
                    )
                result.append(handle)
                # Track the handle
                self._handles[handle.internal_id] = handle
            else:
                raise TypeError(
                    f"Expected ArtifactHandle or str, got {type(h).__name__}"
                )

        return result

    def _infer_step_type(self, func: Callable) -> str:
        """
        Infer step type from function characteristics.

        Uses heuristics based on function name and source code.

        Args:
            func: Function to analyze

        Returns:
            Inferred step type string
        """
        func_name = func.__name__.lower()

        # LLM keywords
        llm_keywords = ["llm", "ai", "gpt", "claude", "openai", "anthropic", "chat", "completion"]
        if any(kw in func_name for kw in llm_keywords):
            return "llm"

        # SQL keywords
        sql_keywords = ["sql", "query", "database", "db"]
        if any(kw in func_name for kw in sql_keywords):
            return "sql"

        # HTTP keywords
        http_keywords = ["http", "api", "request", "fetch", "rest"]
        if any(kw in func_name for kw in http_keywords):
            return "http"

        # Check source code for imports
        try:
            source = inspect.getsource(func)
            if "openai" in source or "anthropic" in source:
                return "llm"
            if "sqlalchemy" in source or "psycopg" in source:
                return "sql"
            if "requests" in source or "httpx" in source:
                return "http"
        except (OSError, TypeError):
            pass

        return "python"

    def _capture_source_location(self) -> str:
        """
        Capture source code location of the registration call.

        Returns:
            Source reference in format "filename.py:line_number"
        """
        try:
            # Walk up the stack to find user code
            frame = inspect.currentframe()
            if frame is None:
                return "<unknown>:0"

            # Go up frames: _capture_source_location -> step_meta -> decorator -> user
            caller_frame = frame
            for _ in range(4):  # Go up 4 frames
                if caller_frame.f_back is None:
                    break
                caller_frame = caller_frame.f_back

            filename = Path(caller_frame.f_code.co_filename).name
            lineno = caller_frame.f_lineno

            return f"{filename}:{lineno}"

        except Exception:
            return "<unknown>:0"

    def _dict_to_identity(self, data: Dict[str, Any]) -> Identity:
        """
        Convert dictionary to Identity object.

        Args:
            data: Dictionary with identity fields

        Returns:
            Identity object
        """
        from stardive.models import UserType, AuthMethod

        return Identity(
            user_id=data.get("user_id", data.get("user", "unknown")),
            user_type=data.get("user_type", UserType.HUMAN),
            display_name=data.get("display_name"),
            auth_method=data.get("auth_method", AuthMethod.NONE),
        )

    def _detect_environment(self) -> EnvironmentFingerprint:
        """
        Auto-detect execution environment.

        Returns:
            EnvironmentFingerprint with current environment details
        """
        import platform
        import os
        import hashlib

        # Try to get git SHA (must be full 40 chars)
        git_sha = None
        git_branch = None
        git_dirty = False
        try:
            import subprocess
            # Get full SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                sha = result.stdout.strip()
                # Validate it's a proper 40-char hex string
                if len(sha) == 40 and all(c in "0123456789abcdef" for c in sha):
                    git_sha = sha

            # Get branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                git_branch = result.stdout.strip()

            # Check if dirty
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                git_dirty = bool(result.stdout.strip())
        except Exception:
            pass

        # Compute dependencies hash from pyproject.toml or requirements.txt
        deps_content = ""
        for deps_file in ["pyproject.toml", "requirements.txt", "setup.py"]:
            if os.path.exists(deps_file):
                try:
                    with open(deps_file, "r") as f:
                        deps_content = f.read()
                    break
                except Exception:
                    pass
        if not deps_content:
            deps_content = f"python:{platform.python_version()}"
        deps_hash = f"sha256:{hashlib.sha256(deps_content.encode()).hexdigest()}"

        # Compute fingerprint hash
        fingerprint_data = f"{git_sha}|{deps_hash}|{platform.python_version()}|{platform.system()}|{platform.machine()}"
        fingerprint_hash = f"sha256:{hashlib.sha256(fingerprint_data.encode()).hexdigest()}"

        return EnvironmentFingerprint(
            git_sha=git_sha,
            git_branch=git_branch,
            git_dirty=git_dirty,
            dependencies_hash=deps_hash,
            python_version=platform.python_version(),
            os=platform.system(),
            os_version=platform.version(),
            arch=platform.machine(),
            fingerprint_hash=fingerprint_hash,
        )

    def _get_executor_ref(self, step_type: str) -> str:
        """
        Get executor reference for a step type.

        Args:
            step_type: Type of step

        Returns:
            Executor module:class reference
        """
        # Map step types to adapters
        executor_map = {
            "python": "stardive.adapters.python:PythonAdapter",
            "llm": "stardive.adapters.llm:LLMAdapter",
            "sql": "stardive.adapters.sql:SQLAdapter",
            "http": "stardive.adapters.http:HTTPAdapter",
            "human_approval": "stardive.adapters.human:ApprovalAdapter",
        }
        return executor_map.get(step_type, "stardive.adapters.python:PythonAdapter")

    # ========================================================================
    # Introspection
    # ========================================================================

    @property
    def step_count(self) -> int:
        """Number of registered steps."""
        return len(self._steps)

    @property
    def step_ids(self) -> List[str]:
        """List of registered step IDs."""
        return list(self._steps.keys())

    def get_step(self, step_id: str) -> Optional[ContextRegisteredStep]:
        """Get a registered step by ID."""
        return self._steps.get(step_id)

    def has_step(self, step_id: str) -> bool:
        """Check if a step is registered."""
        return step_id in self._steps

    @property
    def handle_count(self) -> int:
        """Number of tracked artifact handles."""
        return len(self._handles)

    def clear(self) -> None:
        """Clear all registered steps and handles."""
        self._steps.clear()
        self._handles.clear()
        self._expected_produces.clear()
        self._step_sources.clear()

    def __repr__(self) -> str:
        return (
            f"StardiveContext(name={self._name!r}, "
            f"steps={self.step_count}, handles={self.handle_count})"
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StardiveContext",
    "ContextRegisteredStep",
    "StepIdCollisionError",
    "ArtifactNotProducedError",
    "ProducerStepNotFoundError",
    "CycleDetectedError",
]
