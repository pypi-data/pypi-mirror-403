"""Transition definitions for PyGubernator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pygubernator.core.errors import FSMError


@dataclass(frozen=True, slots=True)
class Transition:
    """Immutable transition definition between states.

    Transitions define the valid paths through the state machine. Each
    transition is triggered by an event and can have guards (conditions)
    that must be satisfied and actions to execute on completion.

    Attributes:
        trigger: Event name that triggers this transition.
        source: Set of valid source state names for this transition.
        dest: Target state name after transition completes.
        guards: Guard function names that must all return True.
        actions: Action names to execute after successful transition.
        description: Human-readable description of this transition.
        metadata: Additional user-defined metadata.

    Example:
        >>> transition = Transition(
        ...     trigger="execution_report",
        ...     source=frozenset({"OPEN", "PARTIALLY_FILLED"}),
        ...     dest="FILLED",
        ...     guards=("is_full_fill",),
        ...     actions=("update_positions", "release_buying_power"),
        ... )
    """

    trigger: str
    source: frozenset[str]
    dest: str
    guards: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trigger:
            raise ValueError("Transition trigger cannot be empty")
        if not self.source:
            raise ValueError("Transition must have at least one source state")
        if not self.dest:
            raise ValueError("Transition destination cannot be empty")

    @classmethod
    def from_single_source(
        cls,
        trigger: str,
        source: str,
        dest: str,
        guards: tuple[str, ...] = (),
        actions: tuple[str, ...] = (),
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "Transition":
        """Create a transition with a single source state."""
        return cls(
            trigger=trigger,
            source=frozenset({source}),
            dest=dest,
            guards=guards,
            actions=actions,
            description=description,
            metadata=metadata or {},
        )

    def matches_source(self, state: str) -> bool:
        """Check if the given state is a valid source for this transition."""
        return state in self.source

    def has_guards(self) -> bool:
        """Check if this transition has guard conditions."""
        return len(self.guards) > 0


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Immutable result of a transition computation.

    This is the output of the FSM engine's process() method. It contains
    all information needed to:
    1. Persist the state change (if successful)
    2. Execute side effects (actions)
    3. Handle errors (if unsuccessful)

    The FSM itself does NOT execute actions or persist state - it only
    computes what SHOULD happen. The caller is responsible for:
    - Persisting the state change atomically
    - Executing actions AFTER successful persistence

    Attributes:
        success: Whether the transition was successful.
        source_state: The state before the transition attempt.
        target_state: The new state (None if transition failed).
        trigger: The event that triggered this transition.
        actions_to_execute: Ordered list of actions to run after persistence.
        on_exit_actions: Exit actions from the source state.
        on_enter_actions: Entry actions for the target state.
        error: Error details if transition failed.
        metadata: Additional context (e.g., guard results, timing).

    Example:
        >>> result = machine.process("OPEN", "execution_report", context)
        >>> if result.success:
        ...     db.update_state(order_id, result.target_state)
        ...     for action in result.all_actions:
        ...         action_registry.execute(action, context)
    """

    success: bool
    source_state: str
    target_state: str | None
    trigger: str
    actions_to_execute: tuple[str, ...] = ()
    on_exit_actions: tuple[str, ...] = ()
    on_enter_actions: tuple[str, ...] = ()
    error: "FSMError | None" = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_actions(self) -> tuple[str, ...]:
        """Get all actions in execution order: exit -> transition -> enter."""
        return self.on_exit_actions + self.actions_to_execute + self.on_enter_actions

    @property
    def is_self_transition(self) -> bool:
        """Check if this is a self-transition (source == target)."""
        return self.success and self.source_state == self.target_state

    @property
    def state_changed(self) -> bool:
        """Check if the state actually changed."""
        return self.success and self.source_state != self.target_state

    @classmethod
    def success_result(
        cls,
        source_state: str,
        target_state: str,
        trigger: str,
        actions: tuple[str, ...] = (),
        on_exit: tuple[str, ...] = (),
        on_enter: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> "TransitionResult":
        """Create a successful transition result."""
        return cls(
            success=True,
            source_state=source_state,
            target_state=target_state,
            trigger=trigger,
            actions_to_execute=actions,
            on_exit_actions=on_exit,
            on_enter_actions=on_enter,
            error=None,
            metadata=metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        source_state: str,
        trigger: str,
        error: "FSMError",
        metadata: dict[str, Any] | None = None,
    ) -> "TransitionResult":
        """Create a failed transition result."""
        return cls(
            success=False,
            source_state=source_state,
            target_state=None,
            trigger=trigger,
            actions_to_execute=(),
            on_exit_actions=(),
            on_enter_actions=(),
            error=error,
            metadata=metadata or {},
        )
