"""Guard evaluation logic for PyGubernator FSM."""

from __future__ import annotations

from typing import Any

from pygubernator.core.errors import GuardNotFoundError, GuardRejectedError
from pygubernator.core.transition import Transition
from pygubernator.guards.registry import GuardRegistry, GuardResult


class GuardEvaluator:
    """Evaluates guard conditions for transitions.

    The evaluator is responsible for determining whether a transition
    should be allowed based on its guard conditions and the current
    context.

    This class provides additional functionality beyond the basic
    registry evaluation:
    - Detailed error reporting
    - Guard expression parsing (future)
    - Guard caching (future)

    Example:
        >>> evaluator = GuardEvaluator(guard_registry)
        >>> result = evaluator.can_transition(transition, context)
        >>> if not result.passed:
        ...     print(f"Blocked by: {result.guard_name}")
    """

    def __init__(
        self,
        registry: GuardRegistry,
        strict: bool = True,
    ) -> None:
        """Initialize the guard evaluator.

        Args:
            registry: Guard registry containing guard functions.
            strict: If True, raise errors for missing guards.
                   If False, missing guards are treated as passing.
        """
        self.registry = registry
        self.strict = strict

    def can_transition(
        self,
        transition: Transition,
        context: dict[str, Any],
    ) -> GuardResult:
        """Check if a transition is allowed based on its guards.

        Args:
            transition: The transition to check.
            context: Context dictionary for guard evaluation.

        Returns:
            GuardResult indicating if transition is allowed.

        Raises:
            GuardNotFoundError: If strict=True and a guard is missing.
        """
        if not transition.guards:
            return GuardResult.success()

        return self._evaluate_guards(transition.guards, context)

    def _evaluate_guards(
        self,
        guards: tuple[str, ...],
        context: dict[str, Any],
    ) -> GuardResult:
        """Evaluate a sequence of guard conditions.

        All guards must pass for the result to be successful (AND logic).
        """
        evaluated: list[tuple[str, bool]] = []

        for guard_name in guards:
            # Handle missing guards based on strict mode
            if not self.registry.has(guard_name):
                if self.strict:
                    raise GuardNotFoundError(
                        f"Guard '{guard_name}' not registered",
                        guard_name=guard_name,
                    )
                # Non-strict: treat missing guard as passing
                evaluated.append((guard_name, True))
                continue

            # Evaluate the guard
            try:
                result = self.registry.evaluate(guard_name, context)
                evaluated.append((guard_name, result))

                if not result:
                    return GuardResult.failure(guard_name, evaluated=evaluated)

            except Exception as e:
                # Guard raised an exception - treat as failure
                evaluated.append((guard_name, False))
                return GuardResult.failure(
                    guard_name,
                    message=f"Guard '{guard_name}' raised exception: {e}",
                    evaluated=evaluated,
                )

        return GuardResult.success(evaluated)

    def evaluate_and_raise(
        self,
        transition: Transition,
        current_state: str,
        context: dict[str, Any],
    ) -> None:
        """Evaluate guards and raise exception if blocked.

        Args:
            transition: The transition to check.
            current_state: The current state name.
            context: Context dictionary for guard evaluation.

        Raises:
            GuardRejectedError: If any guard blocks the transition.
            GuardNotFoundError: If strict=True and a guard is missing.
        """
        result = self.can_transition(transition, context)

        if not result.passed:
            raise GuardRejectedError(
                message=result.message,
                current_state=current_state,
                trigger=transition.trigger,
                guard_name=result.guard_name or "unknown",
                guard_result=result.evaluated_guards,
            )

    def validate_guards_exist(self, guards: tuple[str, ...]) -> list[str]:
        """Check which guards are missing from the registry.

        Args:
            guards: Guard names to check.

        Returns:
            List of missing guard names.
        """
        return [g for g in guards if not self.registry.has(g)]

    def get_required_guards(self, transitions: list[Transition]) -> set[str]:
        """Get all unique guard names from a list of transitions.

        Args:
            transitions: List of transitions to analyze.

        Returns:
            Set of unique guard names.
        """
        guards: set[str] = set()
        for trans in transitions:
            guards.update(trans.guards)
        return guards
