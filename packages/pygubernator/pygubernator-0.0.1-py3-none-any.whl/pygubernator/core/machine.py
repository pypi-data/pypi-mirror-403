"""State Machine engine for PyGubernator FSM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pygubernator.config.loader import ConfigLoader
from pygubernator.core.errors import (
    ConfigurationError,
    ErrorPolicy,
    InvalidTransitionError,
    TerminalStateError,
    UndefinedStateError,
    UndefinedTriggerError,
)
from pygubernator.core.event import Event
from pygubernator.core.state import State, StateType
from pygubernator.core.transition import Transition, TransitionResult
from pygubernator.guards.evaluator import GuardEvaluator
from pygubernator.guards.registry import GuardRegistry


class StateMachine:
    """Pure, stateless finite state machine engine.

    The StateMachine is the core of PyGubernator. It takes a state and event
    as input and computes the resulting state and actions - without
    holding any internal state or executing side effects.

    This design enables:
    - Horizontal scaling (no shared state)
    - Testability (pure functions)
    - Determinism (same input -> same output)
    - Separation of concerns (compute vs persist vs execute)

    The machine is configured via YAML/JSON definitions that specify:
    - States (with types, timeouts, hooks)
    - Transitions (with guards and actions)
    - Error policies

    Example:
        >>> machine = StateMachine.from_yaml("order_fsm.yaml")
        >>> machine.bind_guards(guard_registry)
        >>>
        >>> # Compute transition (pure, no side effects)
        >>> result = machine.process("OPEN", "execution_report", context)
        >>>
        >>> if result.success:
        ...     db.update_state(order_id, result.target_state)  # Persist
        ...     for action in result.all_actions:               # Execute
        ...         action_registry.execute(action, context)
    """

    def __init__(
        self,
        states: dict[str, State],
        transitions: list[Transition],
        meta: dict[str, Any] | None = None,
        error_policy: ErrorPolicy | None = None,
    ) -> None:
        """Initialize the state machine.

        Args:
            states: Dictionary mapping state names to State objects.
            transitions: List of Transition objects.
            meta: Optional metadata (version, machine_name, etc.).
            error_policy: Optional error handling configuration.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        self._states = states
        self._transitions = transitions
        self._meta = meta or {}
        self._error_policy = error_policy or ErrorPolicy()

        # Build transition lookup index
        self._transition_index: dict[tuple[str, str], list[Transition]] = {}
        self._build_transition_index()

        # Guard evaluator (initialized when guards are bound)
        self._guard_registry: GuardRegistry | None = None
        self._guard_evaluator: GuardEvaluator | None = None

        # Validate configuration
        self._validate()

    def _build_transition_index(self) -> None:
        """Build index for fast transition lookup."""
        for transition in self._transitions:
            for source in transition.source:
                key = (source, transition.trigger)
                if key not in self._transition_index:
                    self._transition_index[key] = []
                self._transition_index[key].append(transition)

    def _validate(self) -> None:
        """Validate the state machine configuration."""
        # Check for exactly one initial state
        initial_states = [s for s in self._states.values() if s.is_initial]
        if len(initial_states) == 0:
            raise ConfigurationError(
                "No initial state defined",
                context={"states": list(self._states.keys())},
            )
        if len(initial_states) > 1:
            raise ConfigurationError(
                "Multiple initial states defined",
                context={"initial_states": [s.name for s in initial_states]},
            )

        # Validate transition references
        for trans in self._transitions:
            for source in trans.source:
                if source not in self._states:
                    raise ConfigurationError(
                        f"Transition references undefined source state: {source}",
                        context={"transition": trans.trigger, "source": source},
                    )
            if trans.dest not in self._states:
                raise ConfigurationError(
                    f"Transition references undefined destination state: {trans.dest}",
                    context={"transition": trans.trigger, "dest": trans.dest},
                )

        # Validate timeout destinations
        for state in self._states.values():
            if state.timeout and state.timeout.destination not in self._states:
                raise ConfigurationError(
                    f"State timeout references undefined destination: {state.timeout.destination}",
                    context={"state": state.name},
                )

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        validate: bool = True,
        variables: dict[str, str] | None = None,
    ) -> "StateMachine":
        """Create a StateMachine from a YAML configuration file.

        Args:
            path: Path to the YAML configuration file.
            validate: If True, validate configuration against schema.
            variables: Optional variables for substitution.

        Returns:
            Configured StateMachine instance.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        loader = ConfigLoader(validate=validate, variables=variables)
        config = loader.load(path)
        return cls.from_dict(config)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "StateMachine":
        """Create a StateMachine from a configuration dictionary.

        Args:
            config: Configuration dictionary matching the schema.

        Returns:
            Configured StateMachine instance.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        loader = ConfigLoader(validate=False)
        states, transitions, meta = loader.parse(config)

        # Parse error policy
        error_policy = None
        if "error_policy" in config:
            ep = config["error_policy"]
            error_policy = ErrorPolicy(
                default_fallback=ep.get("default_fallback"),
                retry_attempts=ep.get("retry_attempts", 0),
                strict_mode=meta.get("strict_mode", True),
            )
        else:
            error_policy = ErrorPolicy(strict_mode=meta.get("strict_mode", True))

        return cls(states, transitions, meta, error_policy)

    def bind_guards(self, registry: GuardRegistry) -> "StateMachine":
        """Bind a guard registry to the machine.

        Guards are evaluated during transition processing to determine
        if transitions should be allowed.

        Args:
            registry: Guard registry containing guard functions.

        Returns:
            Self for method chaining.
        """
        self._guard_registry = registry
        self._guard_evaluator = GuardEvaluator(
            registry,
            strict=self._error_policy.strict_mode,
        )
        return self

    def process(
        self,
        current_state: str,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Process an event and compute the resulting transition.

        This is the main entry point for the FSM. It takes the current
        state and event, evaluates guards, and returns the transition
        result - WITHOUT executing any side effects.

        The caller is responsible for:
        1. Persisting the state change (if successful)
        2. Executing actions (after persistence)

        Args:
            current_state: The current state name.
            event: Event trigger (string) or Event object.
            context: Optional context dictionary for guards.

        Returns:
            TransitionResult with the computed transition.

        Raises:
            UndefinedStateError: If current_state is not defined.
        """
        # Normalize event
        if isinstance(event, str):
            trigger = event
            event_obj = Event(trigger=trigger)
        else:
            trigger = event.trigger
            event_obj = event

        # Merge event payload into context
        ctx = context or {}
        ctx = {**ctx, **event_obj.payload, "_event": event_obj}

        # Validate current state exists
        if current_state not in self._states:
            raise UndefinedStateError(
                f"State '{current_state}' is not defined",
                state_name=current_state,
            )

        state = self._states[current_state]

        # Check if terminal state
        if state.is_terminal:
            return TransitionResult.failure_result(
                source_state=current_state,
                trigger=trigger,
                error=TerminalStateError(current_state, trigger),
                metadata={"reason": "terminal_state"},
            )

        # Find matching transitions
        candidates = self._find_transitions(current_state, trigger)

        # Handle no matching transitions
        if not candidates:
            return self._handle_no_transition(current_state, trigger)

        # Evaluate guards and find first valid transition
        for transition in candidates:
            if self._evaluate_guards(transition, current_state, ctx):
                return self._create_success_result(
                    state, transition, trigger, ctx
                )

        # All guards failed
        return self._handle_guard_failure(current_state, trigger, candidates)

    def _find_transitions(
        self, current_state: str, trigger: str
    ) -> list[Transition]:
        """Find all transitions matching state and trigger."""
        key = (current_state, trigger)
        return self._transition_index.get(key, [])

    def _evaluate_guards(
        self,
        transition: Transition,
        current_state: str,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate guards for a transition."""
        if not transition.guards:
            return True

        if self._guard_evaluator is None:
            # No guard registry bound - guards pass by default in non-strict mode
            if self._error_policy.strict_mode:
                raise ConfigurationError(
                    "Guards referenced but no guard registry bound. "
                    "Call bind_guards() before processing events.",
                    context={"guards": transition.guards},
                )
            return True

        result = self._guard_evaluator.can_transition(transition, context)
        return result.passed

    def _create_success_result(
        self,
        source_state: State,
        transition: Transition,
        trigger: str,
        context: dict[str, Any],
    ) -> TransitionResult:
        """Create a successful transition result."""
        target_state = self._states[transition.dest]

        return TransitionResult.success_result(
            source_state=source_state.name,
            target_state=target_state.name,
            trigger=trigger,
            actions=transition.actions,
            on_exit=source_state.on_exit,
            on_enter=target_state.on_enter,
            metadata={
                "transition_description": transition.description,
            },
        )

    def _handle_no_transition(
        self, current_state: str, trigger: str
    ) -> TransitionResult:
        """Handle case where no transition matches."""
        if self._error_policy.strict_mode:
            # Check if trigger exists anywhere in machine
            all_triggers = {t.trigger for t in self._transitions}
            if trigger not in all_triggers:
                error = UndefinedTriggerError(
                    f"Trigger '{trigger}' is not defined in this machine",
                    trigger=trigger,
                    available_triggers=sorted(all_triggers),
                )
            else:
                error = InvalidTransitionError(
                    f"No transition for trigger '{trigger}' from state '{current_state}'",
                    current_state=current_state,
                    trigger=trigger,
                )
            return TransitionResult.failure_result(
                source_state=current_state,
                trigger=trigger,
                error=error,
            )

        # Non-strict mode: return no-op result
        return TransitionResult(
            success=True,
            source_state=current_state,
            target_state=current_state,  # Stay in same state
            trigger=trigger,
            metadata={"no_op": True, "reason": "no_matching_transition"},
        )

    def _handle_guard_failure(
        self,
        current_state: str,
        trigger: str,
        candidates: list[Transition],
    ) -> TransitionResult:
        """Handle case where all guard conditions failed."""
        error = InvalidTransitionError(
            f"All guards failed for trigger '{trigger}' from state '{current_state}'",
            current_state=current_state,
            trigger=trigger,
            context={
                "candidate_count": len(candidates),
                "reason": "guards_failed",
            },
        )
        return TransitionResult.failure_result(
            source_state=current_state,
            trigger=trigger,
            error=error,
            metadata={"reason": "guards_failed"},
        )

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_state(self, name: str) -> State:
        """Get a state by name.

        Args:
            name: State name.

        Returns:
            State object.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        if name not in self._states:
            raise UndefinedStateError(f"State '{name}' is not defined", state_name=name)
        return self._states[name]

    def get_initial_state(self) -> State:
        """Get the initial state.

        Returns:
            The initial state.
        """
        for state in self._states.values():
            if state.is_initial:
                return state
        raise ConfigurationError("No initial state defined")  # Should never happen

    def get_available_transitions(self, current_state: str) -> list[Transition]:
        """Get all transitions available from a state.

        Args:
            current_state: Current state name.

        Returns:
            List of available transitions.
        """
        if current_state not in self._states:
            raise UndefinedStateError(
                f"State '{current_state}' is not defined",
                state_name=current_state,
            )

        available: list[Transition] = []
        for trans in self._transitions:
            if current_state in trans.source:
                available.append(trans)
        return available

    def get_available_triggers(self, current_state: str) -> list[str]:
        """Get all triggers available from a state.

        Args:
            current_state: Current state name.

        Returns:
            List of available trigger names.
        """
        transitions = self.get_available_transitions(current_state)
        return sorted(set(t.trigger for t in transitions))

    def validate_state(self, state: str) -> bool:
        """Check if a state is defined.

        Args:
            state: State name to check.

        Returns:
            True if state is defined, False otherwise.
        """
        return state in self._states

    def is_terminal(self, state: str) -> bool:
        """Check if a state is terminal.

        Args:
            state: State name to check.

        Returns:
            True if state is terminal, False otherwise.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        return self.get_state(state).is_terminal

    def is_initial(self, state: str) -> bool:
        """Check if a state is the initial state.

        Args:
            state: State name to check.

        Returns:
            True if state is initial, False otherwise.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        return self.get_state(state).is_initial

    def can_transition(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if a transition is possible.

        This is a convenience method that processes the event and
        returns whether it would succeed.

        Args:
            current_state: Current state name.
            trigger: Event trigger.
            context: Optional context for guard evaluation.

        Returns:
            True if transition would succeed, False otherwise.
        """
        try:
            result = self.process(current_state, trigger, context)
            return result.success
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Get the machine name from metadata."""
        return self._meta.get("machine_name", "unnamed")

    @property
    def version(self) -> str:
        """Get the machine version from metadata."""
        return self._meta.get("version", "0.0.0")

    @property
    def strict_mode(self) -> bool:
        """Check if strict mode is enabled."""
        return self._error_policy.strict_mode

    @property
    def states(self) -> dict[str, State]:
        """Get all states (read-only view)."""
        return dict(self._states)

    @property
    def transitions(self) -> list[Transition]:
        """Get all transitions (read-only view)."""
        return list(self._transitions)

    @property
    def state_names(self) -> list[str]:
        """Get all state names."""
        return list(self._states.keys())

    @property
    def trigger_names(self) -> list[str]:
        """Get all unique trigger names."""
        return sorted(set(t.trigger for t in self._transitions))

    @property
    def terminal_states(self) -> list[str]:
        """Get all terminal state names."""
        return [s.name for s in self._states.values() if s.is_terminal]

    @property
    def meta(self) -> dict[str, Any]:
        """Get machine metadata."""
        return dict(self._meta)

    def __repr__(self) -> str:
        return (
            f"StateMachine(name={self.name!r}, "
            f"states={len(self._states)}, "
            f"transitions={len(self._transitions)})"
        )
