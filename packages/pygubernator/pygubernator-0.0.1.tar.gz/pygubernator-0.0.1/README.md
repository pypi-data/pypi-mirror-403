# PyGubernator

A configuration-driven, stateless finite state machine library for Python.

PyGubernator defines behavioral contracts through YAML/JSON specifications, computing state transitions without holding internal state. Designed for high-integrity systems like order management, workflow engines, and distributed applications.

## Features

- **Configuration-Driven**: Define state machines in YAML/JSON with schema validation
- **Stateless Design**: Pure computation—takes state in, returns state/actions out
- **Guards**: Conditional transitions based on runtime context
- **Actions/Hooks**: Entry/exit hooks and transition actions
- **Timeouts/TTL**: Automatic transitions after configurable durations
- **Strict Mode**: Contract enforcement for undefined triggers
- **Type-Safe**: Full type hints and PEP 561 compliance

## Installation

```bash
pip install pygubernator
```

For development:

```bash
git clone https://github.com/statfyi/pygubernator
cd pygubernator
pip install -e ".[dev]"
```

## Quick Start

### 1. Define Your State Machine (YAML)

```yaml
# order_fsm.yaml
meta:
  version: "1.0.0"
  machine_name: "order_management"
  strict_mode: true

states:
  - name: PENDING_NEW
    type: initial
    timeout:
      seconds: 5.0
      destination: TIMED_OUT

  - name: OPEN
    type: stable
    on_enter:
      - notify_ui
      - log_audit

  - name: FILLED
    type: terminal

  - name: TIMED_OUT
    type: terminal

transitions:
  - trigger: exchange_ack
    source: PENDING_NEW
    dest: OPEN
    actions:
      - update_order_id

  - trigger: execution_report
    source: OPEN
    dest: FILLED
    guards:
      - is_full_fill
    actions:
      - update_positions
```

### 2. Use the State Machine

```python
from pygubernator import StateMachine, GuardRegistry, ActionRegistry, Event
from pygubernator.actions import ActionExecutor

# Load the FSM definition
machine = StateMachine.from_yaml("order_fsm.yaml")

# Register guards (pure functions for conditions)
guards = GuardRegistry()
guards.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])
machine.bind_guards(guards)

# Register actions (side effects executed after persistence)
actions = ActionRegistry()
actions.register("update_order_id", lambda ctx: update_db(ctx["order_id"]))
actions.register("update_positions", lambda ctx: update_positions(ctx))
actions.register("notify_ui", lambda ctx: send_notification(ctx))
actions.register("log_audit", lambda ctx: log_audit_trail(ctx))

executor = ActionExecutor(actions)

# --- The "Sandwich Pattern" ---

# Phase 1: Receive event
event = Event(trigger="execution_report", payload={"fill_qty": 100, "order_qty": 100})

# Phase 2: Get current state from your database
current_state = db.get_order_state(order_id)  # "OPEN"

# Phase 3: Compute transition (pure, no side effects)
result = machine.process(
    current_state=current_state,
    event=event,
    context={"fill_qty": 100, "order_qty": 100}
)

# Phase 4: Persist atomically
if result.success:
    with db.transaction():
        db.update_order_state(order_id, result.target_state)
        db.insert_audit_trail(order_id, result)

    # Phase 5: Execute side effects (after commit)
    executor.execute(result, context)
```

## Core Concepts

### States

States represent the nodes in your state machine:

```python
from pygubernator import State, StateType, Timeout

state = State(
    name="PENDING_NEW",
    type=StateType.INITIAL,  # initial, stable, terminal, error
    description="Waiting for exchange acknowledgment",
    on_enter=("log_entry",),
    on_exit=("log_exit",),
    timeout=Timeout(seconds=5.0, destination="TIMED_OUT"),
)
```

### Transitions

Transitions define the valid paths between states:

```python
from pygubernator import Transition

transition = Transition(
    trigger="execution_report",
    source=frozenset({"OPEN", "PARTIALLY_FILLED"}),
    dest="FILLED",
    guards=("is_full_fill",),
    actions=("update_positions", "release_buying_power"),
)
```

### Guards

Guards are pure functions that control whether transitions are allowed:

```python
from pygubernator import GuardRegistry, equals, greater_than, all_of

guards = GuardRegistry()

# Simple function
guards.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])

# Built-in guard factories
guards.register("is_valid_amount", greater_than("amount", 0))
guards.register("is_admin", equals("role", "admin"))

# Compound guards
guards.register(
    "can_approve",
    all_of(equals("status", "pending"), greater_than("balance", 1000))
)
```

### Actions

Actions handle side effects and are executed after state persistence:

```python
from pygubernator import ActionRegistry
from pygubernator.actions import ActionExecutor

actions = ActionRegistry()

@actions.decorator()
def send_notification(ctx: dict) -> None:
    email_service.send(ctx["user_email"], "Order updated")

@actions.decorator(name="update_ledger")
def update_ledger_entry(ctx: dict) -> None:
    ledger.record_transaction(ctx["order_id"], ctx["amount"])

# Execute after successful DB commit
executor = ActionExecutor(actions)
execution_result = executor.execute(transition_result, context)
```

### Timeouts

Handle automatic transitions when entities stay in a state too long:

```python
from pygubernator import TimeoutManager, check_timeout
from datetime import datetime, timezone

manager = TimeoutManager(machine)

# Check if order has timed out
entered_at = datetime.fromisoformat(order["entered_pending_at"])
timeout_result = check_timeout(machine, "PENDING_NEW", entered_at)

if timeout_result:
    # Process the timeout transition
    db.update_order_state(order_id, timeout_result.target_state)
```

## The Sandwich Pattern

PyGubernator is designed around the "Load → Decide → Commit → Act" pattern for high-integrity systems:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INGRESS: Receive event, normalize to trigger + payload   │
├─────────────────────────────────────────────────────────────┤
│ 2. HYDRATION: Load current state from database              │
├─────────────────────────────────────────────────────────────┤
│ 3. COMPUTE: machine.process() - pure, no side effects       │
├─────────────────────────────────────────────────────────────┤
│ 4. PERSIST: Atomic DB transaction (state + audit trail)     │
├─────────────────────────────────────────────────────────────┤
│ 5. EXECUTE: Run actions AFTER successful commit             │
└─────────────────────────────────────────────────────────────┘
```

This pattern ensures:
- **Atomicity**: State changes are persisted atomically
- **Idempotency**: Same input always produces same output
- **Recoverability**: Actions can be retried independently
- **Horizontal scaling**: No shared state in the library

## Configuration Schema

PyGubernator validates your YAML/JSON configuration against a JSON Schema:

```yaml
meta:
  version: "1.0.0"        # Semantic version
  machine_name: "my_fsm"  # Unique identifier
  strict_mode: true       # Raise on undefined triggers

states:
  - name: STATE_NAME      # UPPER_SNAKE_CASE
    type: initial|stable|terminal|error
    description: "Human readable"
    on_enter: [action1, action2]
    on_exit: [action3]
    timeout:
      seconds: 5.0
      destination: TIMEOUT_STATE

transitions:
  - trigger: event_name   # lower_snake_case
    source: STATE_A       # or [STATE_A, STATE_B]
    dest: STATE_B
    guards: [guard1, guard2]
    actions: [action1]

error_policy:
  default_fallback: ERROR_STATE
  retry_attempts: 3
```

## API Reference

### StateMachine

```python
# Creation
machine = StateMachine.from_yaml("path/to/config.yaml")
machine = StateMachine.from_dict(config_dict)

# Processing
result = machine.process(current_state, trigger_or_event, context)

# Queries
machine.get_state("STATE_NAME")
machine.get_initial_state()
machine.get_available_transitions("STATE_NAME")
machine.get_available_triggers("STATE_NAME")
machine.validate_state("STATE_NAME")
machine.is_terminal("STATE_NAME")
machine.can_transition("STATE_A", "trigger", context)

# Properties
machine.name
machine.version
machine.states
machine.transitions
machine.state_names
machine.trigger_names
machine.terminal_states
```

### TransitionResult

```python
result = machine.process(state, trigger, context)

result.success           # bool
result.source_state      # str
result.target_state      # str | None
result.trigger           # str
result.actions_to_execute  # tuple[str, ...]
result.on_exit_actions   # tuple[str, ...]
result.on_enter_actions  # tuple[str, ...]
result.all_actions       # tuple[str, ...] (exit + transition + enter)
result.error             # FSMError | None
result.state_changed     # bool
result.is_self_transition  # bool
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=pygubernator --cov-report=term-missing

# Type checking
mypy src/

# Linting & formatting
ruff check .
ruff format .

# Run all checks
make check
```

## License

MIT
