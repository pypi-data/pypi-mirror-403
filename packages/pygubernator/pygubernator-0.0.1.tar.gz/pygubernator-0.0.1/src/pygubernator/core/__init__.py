"""Core FSM components for PyGubernator."""

from __future__ import annotations

from pygubernator.core.state import State, StateType, Timeout
from pygubernator.core.transition import Transition, TransitionResult
from pygubernator.core.event import Event
from pygubernator.core.errors import (
    FSMError,
    ConfigurationError,
    InvalidTransitionError,
    GuardRejectedError,
    UndefinedStateError,
    UndefinedTriggerError,
    TimeoutExpiredError,
)

__all__ = [
    # State
    "State",
    "StateType",
    "Timeout",
    # Transition
    "Transition",
    "TransitionResult",
    # Event
    "Event",
    # Errors
    "FSMError",
    "ConfigurationError",
    "InvalidTransitionError",
    "GuardRejectedError",
    "UndefinedStateError",
    "UndefinedTriggerError",
    "TimeoutExpiredError",
]
