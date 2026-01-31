"""Basic tests for pycatalyst."""

from __future__ import annotations

import pycatalyst


def test_version_is_string() -> None:
    assert isinstance(pycatalyst.__version__, str)
    assert len(pycatalyst.__version__) >= 5  # e.g. 0.1.0
