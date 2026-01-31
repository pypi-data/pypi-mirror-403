"""State definitions for PyGubernator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StateType(str, Enum):
    """Classification of state behavior in the FSM."""

    INITIAL = "initial"
    """The starting state of the machine. Exactly one required."""

    STABLE = "stable"
    """A normal operating state that can transition to other states."""

    TERMINAL = "terminal"
    """An end state. No outbound transitions allowed."""

    ERROR = "error"
    """An error/fallback state for handling failures."""


@dataclass(frozen=True, slots=True)
class Timeout:
    """Timeout configuration for automatic state transitions.

    When a state has a timeout configured, if the entity remains in that state
    for longer than `seconds`, an automatic transition to `destination` should
    be triggered by the external timeout manager.

    Attributes:
        seconds: Duration in seconds before timeout triggers.
        destination: Target state to transition to on timeout.
    """

    seconds: float
    destination: str

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("Timeout seconds must be positive")
        if not self.destination:
            raise ValueError("Timeout destination cannot be empty")


@dataclass(frozen=True, slots=True)
class State:
    """Immutable state definition in the FSM.

    States are the nodes in the state machine graph. Each state has a unique
    name, a type that defines its behavior, and optional hooks for entry/exit
    actions and timeouts.

    Attributes:
        name: Unique identifier for this state.
        type: Classification of state behavior (initial, stable, terminal, error).
        description: Human-readable description of what this state represents.
        on_enter: Action names to execute when entering this state.
        on_exit: Action names to execute when exiting this state.
        timeout: Optional timeout configuration for automatic transitions.
        metadata: Additional user-defined metadata for the state.

    Example:
        >>> state = State(
        ...     name="PENDING_NEW",
        ...     type=StateType.INITIAL,
        ...     description="Order waiting for exchange acknowledgment",
        ...     on_enter=("log_submission",),
        ...     timeout=Timeout(seconds=5.0, destination="TIMED_OUT"),
        ... )
    """

    name: str
    type: StateType = StateType.STABLE
    description: str = ""
    on_enter: tuple[str, ...] = ()
    on_exit: tuple[str, ...] = ()
    timeout: Timeout | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("State name cannot be empty")
        if not self.name.replace("_", "").isalnum():
            raise ValueError(
                f"State name must be alphanumeric with underscores: {self.name}"
            )

    @property
    def is_initial(self) -> bool:
        """Check if this is the initial state."""
        return self.type == StateType.INITIAL

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self.type == StateType.TERMINAL

    @property
    def is_error(self) -> bool:
        """Check if this is an error state."""
        return self.type == StateType.ERROR

    @property
    def has_timeout(self) -> bool:
        """Check if this state has a timeout configured."""
        return self.timeout is not None

    def with_metadata(self, **kwargs: Any) -> "State":
        """Create a new State with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return State(
            name=self.name,
            type=self.type,
            description=self.description,
            on_enter=self.on_enter,
            on_exit=self.on_exit,
            timeout=self.timeout,
            metadata=new_metadata,
        )
