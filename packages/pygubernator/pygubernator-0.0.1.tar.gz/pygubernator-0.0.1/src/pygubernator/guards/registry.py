"""Guard function registry for PyGubernator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from pygubernator.core.errors import GuardNotFoundError


@runtime_checkable
class GuardFunc(Protocol):
    """Protocol for guard functions.

    Guards are pure functions that take a context dictionary and return
    a boolean indicating whether a transition should be allowed.

    The context typically contains:
    - Event payload data
    - Current entity state
    - Additional runtime context

    Guards must be:
    - Pure (no side effects)
    - Deterministic (same input -> same output)
    - Fast (executed during transition computation)
    """

    def __call__(self, context: dict[str, Any]) -> bool:
        """Evaluate the guard condition.

        Args:
            context: Dictionary containing event data and runtime context.

        Returns:
            True if the transition should be allowed, False otherwise.
        """
        ...


@dataclass
class GuardResult:
    """Result of guard evaluation with details.

    Attributes:
        passed: Whether all guards passed.
        guard_name: Name of the guard (last evaluated if failed).
        message: Optional message explaining the result.
        evaluated_guards: List of (guard_name, passed) tuples.
    """

    passed: bool
    guard_name: str | None = None
    message: str = ""
    evaluated_guards: list[tuple[str, bool]] = field(default_factory=list)

    @classmethod
    def success(cls, evaluated: list[tuple[str, bool]] | None = None) -> "GuardResult":
        """Create a successful result."""
        return cls(passed=True, evaluated_guards=evaluated or [])

    @classmethod
    def failure(
        cls,
        guard_name: str,
        message: str = "",
        evaluated: list[tuple[str, bool]] | None = None,
    ) -> "GuardResult":
        """Create a failure result."""
        return cls(
            passed=False,
            guard_name=guard_name,
            message=message or f"Guard '{guard_name}' rejected transition",
            evaluated_guards=evaluated or [],
        )


class GuardRegistry:
    """Registry for guard functions.

    The guard registry stores named guard functions that can be referenced
    in FSM transition definitions. Guards are evaluated during transition
    processing to determine if a transition should be allowed.

    Guards are pure functions: they receive context and return a boolean.
    They should NOT have side effects.

    Example:
        >>> registry = GuardRegistry()
        >>> registry.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])
        >>> registry.register("is_cancellable", is_cancellable_func)
        >>>
        >>> # Evaluate a guard
        >>> result = registry.evaluate("is_full_fill", {"fill_qty": 100, "order_qty": 100})
        >>> assert result is True
    """

    def __init__(self) -> None:
        """Initialize an empty guard registry."""
        self._guards: dict[str, GuardFunc] = {}

    def register(
        self,
        name: str,
        func: GuardFunc | Callable[[dict[str, Any]], bool],
    ) -> None:
        """Register a guard function.

        Args:
            name: Unique name for the guard.
            func: Guard function that takes context and returns bool.

        Raises:
            ValueError: If name is empty or already registered.
        """
        if not name:
            raise ValueError("Guard name cannot be empty")
        if name in self._guards:
            raise ValueError(f"Guard '{name}' is already registered")
        self._guards[name] = func  # type: ignore[assignment]

    def unregister(self, name: str) -> None:
        """Unregister a guard function.

        Args:
            name: Name of the guard to remove.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        if name not in self._guards:
            raise GuardNotFoundError(f"Guard '{name}' not found", guard_name=name)
        del self._guards[name]

    def get(self, name: str) -> GuardFunc:
        """Get a guard function by name.

        Args:
            name: Name of the guard.

        Returns:
            The guard function.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        if name not in self._guards:
            raise GuardNotFoundError(f"Guard '{name}' not found", guard_name=name)
        return self._guards[name]

    def has(self, name: str) -> bool:
        """Check if a guard is registered.

        Args:
            name: Name of the guard.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._guards

    def evaluate(self, name: str, context: dict[str, Any]) -> bool:
        """Evaluate a single guard.

        Args:
            name: Name of the guard to evaluate.
            context: Context dictionary for evaluation.

        Returns:
            Guard evaluation result.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        func = self.get(name)
        return func(context)

    def evaluate_all(
        self,
        guards: tuple[str, ...] | list[str],
        context: dict[str, Any],
        fail_fast: bool = True,
    ) -> GuardResult:
        """Evaluate multiple guards.

        Args:
            guards: Sequence of guard names to evaluate.
            context: Context dictionary for evaluation.
            fail_fast: If True, stop on first failure. If False, evaluate all.

        Returns:
            GuardResult with evaluation details.

        Raises:
            GuardNotFoundError: If any guard is not registered.
        """
        if not guards:
            return GuardResult.success()

        evaluated: list[tuple[str, bool]] = []

        for guard_name in guards:
            result = self.evaluate(guard_name, context)
            evaluated.append((guard_name, result))

            if not result:
                if fail_fast:
                    return GuardResult.failure(guard_name, evaluated=evaluated)

        # Check if any failed (when not fail_fast)
        for name, passed in evaluated:
            if not passed:
                return GuardResult.failure(name, evaluated=evaluated)

        return GuardResult.success(evaluated)

    def list_guards(self) -> list[str]:
        """List all registered guard names.

        Returns:
            List of guard names.
        """
        return list(self._guards.keys())

    def clear(self) -> None:
        """Remove all registered guards."""
        self._guards.clear()

    def __len__(self) -> int:
        """Return number of registered guards."""
        return len(self._guards)

    def __contains__(self, name: str) -> bool:
        """Check if guard is registered."""
        return name in self._guards

    def decorator(
        self, name: str | None = None
    ) -> Callable[[Callable[[dict[str, Any]], bool]], Callable[[dict[str, Any]], bool]]:
        """Decorator to register a guard function.

        Args:
            name: Optional name for the guard. If None, uses function name.

        Returns:
            Decorator function.

        Example:
            >>> registry = GuardRegistry()
            >>> @registry.decorator()
            ... def is_valid(ctx: dict) -> bool:
            ...     return ctx.get("valid", False)
        """

        def decorator_inner(
            func: Callable[[dict[str, Any]], bool],
        ) -> Callable[[dict[str, Any]], bool]:
            guard_name = name or func.__name__
            self.register(guard_name, func)
            return func

        return decorator_inner
