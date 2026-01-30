"""
Step Registry - Registration and management of SDK-defined workflow steps.

This module provides the StepRegistry class which tracks functions registered
via SDK patterns (decorators, context managers, explicit API) before compilation.

The registry acts as an intermediate layer between user registration and
canonical IR compilation:

    User Code → StepRegistry → SDKCompiler → RunPlan

Key Features:
- Track registered steps with metadata
- Capture source code locations for provenance
- Infer step types from function characteristics
- Validate dependencies before compilation
- Support multi-file workflow registration

For canonical IR, see: stardive.kernel.compiler.SDKCompiler
"""

import inspect
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .models import RegisteredStep


# ============================================================================
# Step Registry
# ============================================================================


class StepRegistry:
    """
    Registry for SDK-registered workflow steps.

    Purpose:
        StepRegistry provides a mutable container for collecting step
        definitions before compilation. It captures:
        - Function references and metadata
        - Dependency relationships
        - Source code locations (file:line)
        - Step type hints

        When all steps are registered, SDKCompiler converts the registry
        to a canonical RunPlan.

    Usage Patterns:

        Decorator Pattern (global registry):
            registry = StepRegistry()

            @decorator_using_registry
            def my_step():
                pass

            compiler = SDKCompiler(registry)
            plan = compiler.compile(initiator)

        Context Manager Pattern (per-context registry):
            ctx = StardiveContext()  # Creates internal registry
            @ctx.register_step(...)
            def my_step():
                pass

            plan = ctx.compile()  # Uses internal registry

        Explicit API Pattern (per-instance registry):
            sd = Stardive()  # Creates internal registry
            sd.define_step(...)
            plan = sd.compile()  # Uses internal registry

    Thread Safety:
        StepRegistry is NOT thread-safe. Each thread should use its own
        registry instance (via context or explicit API).

    Examples:
        Basic registration:
            registry = StepRegistry()

            def analyze(data):
                return process(data)

            registry.register(
                step_id="analyze",
                function=analyze,
                depends_on=["fetch"],
                step_type="python",
                config={}
            )

        With type inference:
            def ai_analyze(data):  # 'ai' in name
                return llm_call(data)

            registry.register(
                step_id="ai_step",
                function=ai_analyze,
                depends_on=[],
                step_type=None  # Will infer "llm"
            )

        Cross-module registration:
            # module1.py
            registry = StepRegistry()
            registry.register("step1", func1, [])

            # module2.py
            registry.register("step2", func2, ["step1"])

            # All steps tracked in same registry
    """

    def __init__(self):
        """Initialize an empty step registry."""
        self._steps: Dict[str, RegisteredStep] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._source_refs: Dict[str, str] = {}

    def register(
        self,
        step_id: str,
        function: Callable,
        depends_on: List[str],
        step_type: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> None:
        """
        Register a function as a workflow step.

        This method captures all metadata about a step before compilation:
        - The function to execute
        - Dependencies on other steps
        - Step type (inferred if not provided)
        - Configuration parameters
        - Source code location (for audit trail)

        Args:
            step_id: Unique identifier for this step
            function: Python function to execute for this step
            depends_on: List of step IDs this step depends on
            step_type: Type of step (python, llm, sql, http). Inferred if None.
            config: Step-specific configuration dict

        Raises:
            ValueError: If step_id already registered (duplicates not allowed)
            ValueError: If function is not callable

        Examples:
            Register simple Python function:
                registry.register(
                    step_id="process",
                    function=process_data,
                    depends_on=[],
                    step_type="python"
                )

            Register with dependencies:
                registry.register(
                    step_id="validate",
                    function=validate_results,
                    depends_on=["process", "fetch"],
                    step_type="python"
                )

            Register with config:
                registry.register(
                    step_id="query",
                    function=run_query,
                    depends_on=["connect"],
                    step_type="sql",
                    config={"query": "SELECT * FROM users"}
                )

            Auto-infer step type:
                def llm_analysis(data):
                    return openai.chat(...)

                registry.register(
                    step_id="ai",
                    function=llm_analysis,
                    depends_on=[],
                    step_type=None  # Will infer "llm"
                )
        """
        # Check for duplicate step_id
        if step_id in self._steps:
            raise ValueError(
                f"Step '{step_id}' already registered. "
                f"Duplicate step IDs are not allowed."
            )

        # Validate function is callable
        if not callable(function):
            raise ValueError(
                f"Step '{step_id}': function must be callable, "
                f"got {type(function).__name__}"
            )

        # Infer step type if not provided
        if step_type is None:
            step_type = self._infer_step_type(function)

        # Default empty config
        if config is None:
            config = {}

        # Capture source location for provenance
        source_ref = self._capture_source_location()

        # Create RegisteredStep
        registered_step = RegisteredStep(
            step_id=step_id,
            function=function,
            step_type=step_type,
            config=config,
            source_ref=source_ref,
        )

        # Store in registry
        self._steps[step_id] = registered_step
        self._dependencies[step_id] = depends_on.copy()
        self._source_refs[step_id] = source_ref

    def _infer_step_type(self, function: Callable) -> str:
        """
        Infer step type from function characteristics.

        Uses heuristics based on function name and source code:
        - Name contains 'llm', 'ai', 'gpt', 'claude' → "llm"
        - Name contains 'sql', 'query', 'database' → "sql"
        - Name contains 'http', 'api', 'request' → "http"
        - Source contains 'openai' or 'anthropic' → "llm"
        - Default → "python"

        Args:
            function: Function to analyze

        Returns:
            Inferred step type string

        Examples:
            >>> def llm_analysis(data):
            ...     return result
            >>> registry._infer_step_type(llm_analysis)
            'llm'

            >>> def query_database(sql):
            ...     return rows
            >>> registry._infer_step_type(query_database)
            'sql'

            >>> def process_data(data):
            ...     return cleaned
            >>> registry._infer_step_type(process_data)
            'python'
        """
        # Check function name for keywords
        func_name = function.__name__.lower()

        # LLM keywords
        llm_keywords = ["llm", "ai", "gpt", "claude", "openai", "anthropic"]
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
            source = inspect.getsource(function)
            if "openai" in source or "anthropic" in source:
                return "llm"
            if "sqlalchemy" in source or "psycopg" in source:
                return "sql"
            if "requests" in source or "httpx" in source:
                return "http"
        except (OSError, TypeError):
            # Can't get source (built-in, C extension, etc.)
            pass

        # Default to python
        return "python"

    def _capture_source_location(self) -> str:
        """
        Capture source code location of the registration call.

        This uses the call stack to find where register() was called from,
        providing provenance for audit trails.

        Returns:
            Source reference in format "filename.py:line_number"

        Examples:
            If called from /path/to/workflow.py line 42:
                Returns: "workflow.py:42"

            If called from interactive shell:
                Returns: "<unknown>:0"
        """
        try:
            # Walk up the stack to find the caller
            # 0: _capture_source_location
            # 1: register
            # 2: decorator/context/api (what we want)
            # 3: user code (even better)
            frame = inspect.currentframe()
            if frame is None:
                return "<unknown>:0"

            # Go up 3 frames to get to user code
            caller_frame = frame.f_back.f_back.f_back
            if caller_frame is None:
                return "<unknown>:0"

            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno

            # Get just the filename (not full path)
            filename = Path(filename).name

            return f"{filename}:{lineno}"

        except Exception:
            # If anything goes wrong, return unknown
            return "<unknown>:0"

    def get_step(self, step_id: str) -> Optional[RegisteredStep]:
        """
        Get a registered step by ID.

        Args:
            step_id: Step identifier to look up

        Returns:
            RegisteredStep if found, None otherwise
        """
        return self._steps.get(step_id)

    def has_step(self, step_id: str) -> bool:
        """
        Check if a step is registered.

        Args:
            step_id: Step identifier to check

        Returns:
            True if step is registered, False otherwise
        """
        return step_id in self._steps

    def get_all_steps(self) -> Dict[str, RegisteredStep]:
        """
        Get all registered steps.

        Returns:
            Dictionary mapping step_id to RegisteredStep
        """
        return self._steps.copy()

    def get_dependencies(self, step_id: str) -> List[str]:
        """
        Get dependencies for a step.

        Args:
            step_id: Step identifier

        Returns:
            List of step IDs this step depends on (empty if no dependencies)
        """
        return self._dependencies.get(step_id, []).copy()

    def get_all_dependencies(self) -> Dict[str, List[str]]:
        """
        Get dependency graph for all steps.

        Returns:
            Dictionary mapping step_id to list of dependencies
        """
        return {k: v.copy() for k, v in self._dependencies.items()}

    def clear(self) -> None:
        """
        Clear all registered steps.

        Useful for testing or resetting registry state.
        """
        self._steps.clear()
        self._dependencies.clear()
        self._source_refs.clear()

    @property
    def step_count(self) -> int:
        """Number of registered steps."""
        return len(self._steps)

    def __repr__(self) -> str:
        """String representation of registry."""
        return f"StepRegistry(steps={self.step_count})"


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StepRegistry",
]
