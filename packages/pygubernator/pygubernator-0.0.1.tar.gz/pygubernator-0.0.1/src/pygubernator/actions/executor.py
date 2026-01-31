"""Action execution management for PyGubernator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import logging

from pygubernator.actions.registry import ActionRegistry, ActionResult
from pygubernator.core.transition import TransitionResult


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Complete result of executing all actions from a transition.

    Attributes:
        transition_result: The original transition result.
        action_results: Results from executing each action.
        all_succeeded: Whether all actions succeeded.
        failed_actions: List of action names that failed.
        started_at: When execution started.
        completed_at: When execution completed.
    """

    transition_result: TransitionResult
    action_results: list[ActionResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def all_succeeded(self) -> bool:
        """Check if all actions succeeded."""
        return all(r.success for r in self.action_results)

    @property
    def failed_actions(self) -> list[str]:
        """Get list of failed action names."""
        return [r.action_name for r in self.action_results if not r.success]

    @property
    def succeeded_actions(self) -> list[str]:
        """Get list of succeeded action names."""
        return [r.action_name for r in self.action_results if r.success]

    @property
    def duration_ms(self) -> float | None:
        """Get execution duration in milliseconds."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() * 1000


class ActionExecutor:
    """Executes actions from transition results.

    The executor handles the "Phase 5" of the sandwich pattern:
    executing side effects AFTER state changes have been persisted.

    It provides:
    - Ordered action execution
    - Error isolation (one failure doesn't stop others)
    - Execution tracking and logging
    - Retry support (optional)

    Example:
        >>> executor = ActionExecutor(action_registry)
        >>>
        >>> # After DB commit
        >>> if transition_result.success:
        ...     execution = executor.execute(transition_result, context)
        ...     if not execution.all_succeeded:
        ...         logger.warning(f"Failed actions: {execution.failed_actions}")
    """

    def __init__(
        self,
        registry: ActionRegistry,
        stop_on_error: bool = False,
        log_execution: bool = True,
    ) -> None:
        """Initialize the action executor.

        Args:
            registry: Action registry containing action functions.
            stop_on_error: If True, stop execution on first failure.
            log_execution: If True, log action execution details.
        """
        self.registry = registry
        self.stop_on_error = stop_on_error
        self.log_execution = log_execution

    def execute(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute all actions from a transition result.

        Actions are executed in order:
        1. on_exit actions (from source state)
        2. transition actions
        3. on_enter actions (to target state)

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.

        Returns:
            ExecutionResult with details of all action executions.
        """
        result = ExecutionResult(
            transition_result=transition_result,
            started_at=datetime.now(timezone.utc),
        )

        if not transition_result.success:
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Get all actions in execution order
        all_actions = transition_result.all_actions

        if self.log_execution and all_actions:
            logger.info(
                f"Executing {len(all_actions)} actions for transition "
                f"{transition_result.source_state} -> {transition_result.target_state}"
            )

        # Execute actions
        for action_name in all_actions:
            action_result = self._execute_single(action_name, context)
            result.action_results.append(action_result)

            if not action_result.success and self.stop_on_error:
                if self.log_execution:
                    logger.error(
                        f"Action '{action_name}' failed, stopping execution: "
                        f"{action_result.error}"
                    )
                break

        result.completed_at = datetime.now(timezone.utc)

        if self.log_execution:
            if result.all_succeeded:
                logger.info(
                    f"All {len(all_actions)} actions completed successfully "
                    f"in {result.duration_ms:.2f}ms"
                )
            else:
                logger.warning(
                    f"Action execution completed with failures: {result.failed_actions}"
                )

        return result

    def _execute_single(
        self,
        action_name: str,
        context: dict[str, Any],
    ) -> ActionResult:
        """Execute a single action with error handling.

        Args:
            action_name: Name of the action to execute.
            context: Context dictionary.

        Returns:
            ActionResult with execution details.
        """
        if not self.registry.has(action_name):
            if self.log_execution:
                logger.warning(f"Action '{action_name}' not registered, skipping")
            return ActionResult.ok(action_name, result="skipped_not_registered")

        try:
            if self.log_execution:
                logger.debug(f"Executing action: {action_name}")

            result = self.registry.execute(action_name, context)

            if self.log_execution:
                if result.success:
                    logger.debug(f"Action '{action_name}' completed successfully")
                else:
                    logger.warning(f"Action '{action_name}' failed: {result.error}")

            return result

        except Exception as e:
            if self.log_execution:
                logger.exception(f"Action '{action_name}' raised exception: {e}")
            return ActionResult.fail(action_name, e)

    def execute_specific(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a specific list of actions.

        Useful for retrying failed actions or executing ad-hoc action sequences.

        Args:
            actions: List of action names to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []

        for action_name in actions:
            result = self._execute_single(action_name, context)
            results.append(result)

            if not result.success and self.stop_on_error:
                break

        return results

    def validate_actions_exist(
        self,
        transition_result: TransitionResult,
    ) -> list[str]:
        """Check which actions from a transition are missing.

        Args:
            transition_result: The transition result to check.

        Returns:
            List of missing action names.
        """
        all_actions = transition_result.all_actions
        return [a for a in all_actions if not self.registry.has(a)]
