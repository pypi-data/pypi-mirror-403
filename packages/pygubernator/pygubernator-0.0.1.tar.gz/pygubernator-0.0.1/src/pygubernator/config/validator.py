"""Configuration validation for PyGubernator FSM definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pygubernator.core.errors import ConfigurationError

# Schema directory path
SCHEMA_DIR = Path(__file__).parent / "schemas"


class ConfigValidator:
    """Validates FSM configuration against JSON Schema.

    This validator ensures that YAML/JSON configurations conform to the
    PyGubernator schema before attempting to build a state machine.

    The validator performs two levels of validation:
    1. Schema validation (structure and types)
    2. Semantic validation (references, uniqueness, consistency)

    Example:
        >>> validator = ConfigValidator()
        >>> errors = validator.validate(config)
        >>> if errors:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """

    def __init__(self, schema_path: Path | str | None = None) -> None:
        """Initialize the validator with a schema.

        Args:
            schema_path: Path to the JSON schema file. If None, uses the
                        default machine.json schema.
        """
        self._schema_path = Path(schema_path) if schema_path else SCHEMA_DIR / "machine.json"
        self._schema: dict[str, Any] | None = None
        self._jsonschema_available = self._check_jsonschema()

    def _check_jsonschema(self) -> bool:
        """Check if jsonschema library is available."""
        try:
            import jsonschema  # noqa: F401

            return True
        except ImportError:
            return False

    def _load_schema(self) -> dict[str, Any]:
        """Load the JSON schema from file."""
        if self._schema is None:
            if not self._schema_path.exists():
                raise ConfigurationError(
                    f"Schema file not found: {self._schema_path}",
                    path=str(self._schema_path),
                )
            with open(self._schema_path) as f:
                self._schema = json.load(f)
        return self._schema

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Validate configuration against schema.

        Args:
            config: The configuration dictionary to validate.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []

        # Schema validation (if jsonschema available)
        if self._jsonschema_available:
            errors.extend(self._validate_schema(config))

        # Semantic validation (always performed)
        errors.extend(self._validate_semantics(config))

        return errors

    def _validate_schema(self, config: dict[str, Any]) -> list[str]:
        """Validate against JSON Schema."""
        import jsonschema

        errors: list[str] = []
        schema = self._load_schema()

        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(config):
            path = ".".join(str(p) for p in error.absolute_path) or "root"
            errors.append(f"[{path}] {error.message}")

        return errors

    def _validate_semantics(self, config: dict[str, Any]) -> list[str]:
        """Validate semantic rules that JSON Schema cannot express."""
        errors: list[str] = []

        states = config.get("states", [])
        transitions = config.get("transitions", [])

        # Collect state names
        state_names: set[str] = set()
        initial_states: list[str] = []

        for state in states:
            name = state.get("name", "")
            if name in state_names:
                errors.append(f"Duplicate state name: '{name}'")
            state_names.add(name)

            if state.get("type") == "initial":
                initial_states.append(name)

        # Must have exactly one initial state
        if len(initial_states) == 0:
            errors.append("No initial state defined. Exactly one state must have type='initial'")
        elif len(initial_states) > 1:
            errors.append(
                f"Multiple initial states defined: {initial_states}. "
                "Exactly one state must have type='initial'"
            )

        # Validate transitions reference valid states
        for i, trans in enumerate(transitions):
            trigger = trans.get("trigger", f"transition[{i}]")

            # Check source states
            source = trans.get("source", [])
            if isinstance(source, str):
                source = [source]
            for src in source:
                if src not in state_names:
                    errors.append(
                        f"Transition '{trigger}': source state '{src}' not defined"
                    )

            # Check destination state
            dest = trans.get("dest", "")
            if dest not in state_names:
                errors.append(
                    f"Transition '{trigger}': destination state '{dest}' not defined"
                )

        # Validate timeout destinations
        for state in states:
            timeout = state.get("timeout")
            if timeout:
                dest = timeout.get("destination", "")
                if dest and dest not in state_names:
                    errors.append(
                        f"State '{state.get('name')}': timeout destination '{dest}' not defined"
                    )

        # Validate error policy fallback
        error_policy = config.get("error_policy", {})
        fallback = error_policy.get("default_fallback")
        if fallback and fallback not in state_names:
            errors.append(f"Error policy: fallback state '{fallback}' not defined")

        # Check for transitions from terminal states
        terminal_states = {s.get("name") for s in states if s.get("type") == "terminal"}
        for trans in transitions:
            source = trans.get("source", [])
            if isinstance(source, str):
                source = [source]
            for src in source:
                if src in terminal_states:
                    errors.append(
                        f"Transition '{trans.get('trigger')}': "
                        f"cannot have transitions from terminal state '{src}'"
                    )

        return errors

    def validate_strict(self, config: dict[str, Any]) -> None:
        """Validate and raise ConfigurationError if invalid.

        Args:
            config: The configuration dictionary to validate.

        Raises:
            ConfigurationError: If validation fails.
        """
        errors = self.validate(config)
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed with {len(errors)} error(s)",
                context={"errors": errors},
            )


def validate_config(config: dict[str, Any], strict: bool = True) -> list[str]:
    """Validate a configuration dictionary.

    Convenience function for quick validation.

    Args:
        config: The configuration dictionary to validate.
        strict: If True, raises ConfigurationError on failure.

    Returns:
        List of validation error messages.

    Raises:
        ConfigurationError: If strict=True and validation fails.
    """
    validator = ConfigValidator()
    if strict:
        validator.validate_strict(config)
        return []
    return validator.validate(config)
