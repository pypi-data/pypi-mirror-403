"""Basic tests for pygubernator."""

from __future__ import annotations

import pygubernator


def test_version_is_string() -> None:
    assert isinstance(pygubernator.__version__, str)
    assert len(pygubernator.__version__) >= 5  # e.g. 0.1.0
