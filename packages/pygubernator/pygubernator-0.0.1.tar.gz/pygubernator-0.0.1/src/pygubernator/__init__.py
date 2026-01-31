"""PyGubernator - Configuration-Driven Finite State Machine Library.

PyGubernator is a pure, stateless FSM library that defines behavioral contracts
through YAML/JSON specifications. It computes state transitions without
holding internal state, making it ideal for distributed systems.

Key Features:
- Configuration-driven state machine definitions
- Pure computation (no side effects during processing)
- Guards for conditional transitions
- Actions/hooks for state entry/exit and transitions
- Timeout/TTL support for automatic transitions
- Strict mode for contract enforcement

Example:
    >>> from pygubernator import StateMachine, GuardRegistry
    >>>
    >>> # Load FSM from YAML
    >>> machine = StateMachine.from_yaml("order_fsm.yaml")
    >>>
    >>> # Register guards
    >>> guards = GuardRegistry()
    >>> guards.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])
    >>> machine.bind_guards(guards)
    >>>
    >>> # Process an event (pure computation)
    >>> result = machine.process("OPEN", "execution_report", {"fill_qty": 100, "order_qty": 100})
    >>>
    >>> # Handle result
    >>> if result.success:
    ...     print(f"Transition: {result.source_state} -> {result.target_state}")
    ...     print(f"Actions to execute: {result.all_actions}")
"""

from __future__ import annotations

try:
    from importlib.metadata import version

    __version__ = version("pygubernator")
except Exception:
    __version__ = "0.1.0"

# Core classes
from pygubernator.core.machine import StateMachine
from pygubernator.core.state import State, StateType, Timeout
from pygubernator.core.transition import Transition, TransitionResult
from pygubernator.core.event import Event

# Error classes
from pygubernator.core.errors import (
    FSMError,
    ConfigurationError,
    InvalidTransitionError,
    GuardRejectedError,
    UndefinedStateError,
    UndefinedTriggerError,
    TimeoutExpiredError,
    GuardNotFoundError,
    ActionNotFoundError,
    TerminalStateError,
    ErrorPolicy,
)

# Guard system
from pygubernator.guards.registry import GuardRegistry, GuardFunc, GuardResult
from pygubernator.guards.evaluator import GuardEvaluator
from pygubernator.guards.builtins import (
    register_builtins,
    always_true,
    always_false,
    is_not_none,
    is_truthy,
    equals,
    not_equals,
    greater_than,
    less_than,
    greater_or_equal,
    less_or_equal,
    in_list,
    not_in_list,
    has_key,
    all_of,
    any_of,
    none_of,
    negate,
)

# Action system
from pygubernator.actions.registry import ActionRegistry, ActionFunc, ActionResult
from pygubernator.actions.executor import ActionExecutor, ExecutionResult

# Configuration
from pygubernator.config.loader import ConfigLoader, load_config
from pygubernator.config.validator import ConfigValidator, validate_config

# Timeout management
from pygubernator.timeout.manager import (
    TimeoutManager,
    TimeoutInfo,
    check_timeout,
    get_timeout_info,
)

# Utilities
from pygubernator.utils.serialization import (
    serialize_state,
    deserialize_state,
    serialize_transition_result,
    deserialize_transition_result,
)

__all__ = [
    # Version
    "__version__",
    # Core classes
    "StateMachine",
    "State",
    "StateType",
    "Timeout",
    "Transition",
    "TransitionResult",
    "Event",
    # Errors
    "FSMError",
    "ConfigurationError",
    "InvalidTransitionError",
    "GuardRejectedError",
    "UndefinedStateError",
    "UndefinedTriggerError",
    "TimeoutExpiredError",
    "GuardNotFoundError",
    "ActionNotFoundError",
    "TerminalStateError",
    "ErrorPolicy",
    # Guards
    "GuardRegistry",
    "GuardFunc",
    "GuardResult",
    "GuardEvaluator",
    "register_builtins",
    "always_true",
    "always_false",
    "is_not_none",
    "is_truthy",
    "equals",
    "not_equals",
    "greater_than",
    "less_than",
    "greater_or_equal",
    "less_or_equal",
    "in_list",
    "not_in_list",
    "has_key",
    "all_of",
    "any_of",
    "none_of",
    "negate",
    # Actions
    "ActionRegistry",
    "ActionFunc",
    "ActionResult",
    "ActionExecutor",
    "ExecutionResult",
    # Configuration
    "ConfigLoader",
    "ConfigValidator",
    "load_config",
    "validate_config",
    # Timeout
    "TimeoutManager",
    "TimeoutInfo",
    "check_timeout",
    "get_timeout_info",
    # Utilities
    "serialize_state",
    "deserialize_state",
    "serialize_transition_result",
    "deserialize_transition_result",
]
