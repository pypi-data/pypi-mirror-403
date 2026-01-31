"""Action function registry for PyGubernator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from pygubernator.core.errors import ActionNotFoundError


@runtime_checkable
class ActionFunc(Protocol):
    """Protocol for action functions.

    Actions are functions executed AFTER a transition has been persisted.
    They handle side effects like:
    - Sending notifications
    - Updating external systems
    - Logging/auditing
    - Publishing events

    Unlike guards, actions:
    - CAN have side effects
    - Are executed AFTER state persistence
    - Should be idempotent when possible
    - Should handle their own error recovery
    """

    def __call__(self, context: dict[str, Any]) -> Any:
        """Execute the action.

        Args:
            context: Dictionary containing event data and runtime context.

        Returns:
            Optional result of the action (for logging/debugging).
        """
        ...


@dataclass
class ActionResult:
    """Result of action execution.

    Attributes:
        success: Whether the action executed successfully.
        action_name: Name of the action.
        result: Return value from the action (if any).
        error: Exception if action failed.
    """

    success: bool
    action_name: str
    result: Any = None
    error: Exception | None = None

    @classmethod
    def ok(cls, action_name: str, result: Any = None) -> "ActionResult":
        """Create a successful result."""
        return cls(success=True, action_name=action_name, result=result)

    @classmethod
    def fail(cls, action_name: str, error: Exception) -> "ActionResult":
        """Create a failure result."""
        return cls(success=False, action_name=action_name, error=error)


class ActionRegistry:
    """Registry for action functions.

    The action registry stores named action functions that are executed
    after successful state transitions. Actions handle side effects and
    are explicitly separated from the pure FSM computation.

    IMPORTANT: Actions are executed AFTER the state change has been
    persisted. This ensures that:
    1. State changes are atomic
    2. Actions can be retried independently
    3. Failures don't roll back state changes

    Example:
        >>> registry = ActionRegistry()
        >>> registry.register("notify_user", send_notification)
        >>> registry.register("update_ledger", update_ledger_func)
        >>>
        >>> # Execute actions after state persistence
        >>> for action_name in result.actions_to_execute:
        ...     registry.execute(action_name, context)
    """

    def __init__(self) -> None:
        """Initialize an empty action registry."""
        self._actions: dict[str, ActionFunc] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: ActionFunc | Callable[[dict[str, Any]], Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register an action function.

        Args:
            name: Unique name for the action.
            func: Action function that takes context and performs side effects.
            metadata: Optional metadata about the action (description, tags, etc.).

        Raises:
            ValueError: If name is empty or already registered.
        """
        if not name:
            raise ValueError("Action name cannot be empty")
        if name in self._actions:
            raise ValueError(f"Action '{name}' is already registered")
        self._actions[name] = func  # type: ignore[assignment]
        self._metadata[name] = metadata or {}

    def unregister(self, name: str) -> None:
        """Unregister an action function.

        Args:
            name: Name of the action to remove.

        Raises:
            ActionNotFoundError: If action is not registered.
        """
        if name not in self._actions:
            raise ActionNotFoundError(f"Action '{name}' not found", action_name=name)
        del self._actions[name]
        del self._metadata[name]

    def get(self, name: str) -> ActionFunc:
        """Get an action function by name.

        Args:
            name: Name of the action.

        Returns:
            The action function.

        Raises:
            ActionNotFoundError: If action is not registered.
        """
        if name not in self._actions:
            raise ActionNotFoundError(f"Action '{name}' not found", action_name=name)
        return self._actions[name]

    def has(self, name: str) -> bool:
        """Check if an action is registered.

        Args:
            name: Name of the action.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._actions

    def execute(
        self,
        name: str,
        context: dict[str, Any],
        raise_on_error: bool = False,
    ) -> ActionResult:
        """Execute a single action.

        Args:
            name: Name of the action to execute.
            context: Context dictionary for execution.
            raise_on_error: If True, re-raise action exceptions.

        Returns:
            ActionResult with execution details.

        Raises:
            ActionNotFoundError: If action is not registered.
            Exception: If raise_on_error=True and action fails.
        """
        func = self.get(name)

        try:
            result = func(context)
            return ActionResult.ok(name, result)
        except Exception as e:
            if raise_on_error:
                raise
            return ActionResult.fail(name, e)

    def execute_all(
        self,
        actions: tuple[str, ...] | list[str],
        context: dict[str, Any],
        stop_on_error: bool = False,
    ) -> list[ActionResult]:
        """Execute multiple actions in order.

        Args:
            actions: Sequence of action names to execute.
            context: Context dictionary for execution.
            stop_on_error: If True, stop on first failure.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []

        for action_name in actions:
            try:
                result = self.execute(action_name, context)
                results.append(result)

                if not result.success and stop_on_error:
                    break
            except ActionNotFoundError as e:
                results.append(ActionResult.fail(action_name, e))
                if stop_on_error:
                    break

        return results

    def list_actions(self) -> list[str]:
        """List all registered action names.

        Returns:
            List of action names.
        """
        return list(self._actions.keys())

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for an action.

        Args:
            name: Name of the action.

        Returns:
            Metadata dictionary.

        Raises:
            ActionNotFoundError: If action is not registered.
        """
        if name not in self._metadata:
            raise ActionNotFoundError(f"Action '{name}' not found", action_name=name)
        return self._metadata[name]

    def clear(self) -> None:
        """Remove all registered actions."""
        self._actions.clear()
        self._metadata.clear()

    def __len__(self) -> int:
        """Return number of registered actions."""
        return len(self._actions)

    def __contains__(self, name: str) -> bool:
        """Check if action is registered."""
        return name in self._actions

    def decorator(
        self,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Callable[[Callable[[dict[str, Any]], Any]], Callable[[dict[str, Any]], Any]]:
        """Decorator to register an action function.

        Args:
            name: Optional name for the action. If None, uses function name.
            metadata: Optional metadata about the action.

        Returns:
            Decorator function.

        Example:
            >>> registry = ActionRegistry()
            >>> @registry.decorator()
            ... def notify_user(ctx: dict) -> None:
            ...     send_email(ctx["user_email"], "Order updated")
        """

        def decorator_inner(
            func: Callable[[dict[str, Any]], Any],
        ) -> Callable[[dict[str, Any]], Any]:
            action_name = name or func.__name__
            self.register(action_name, func, metadata)
            return func

        return decorator_inner
