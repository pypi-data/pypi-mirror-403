"""Pytest configuration and fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_dym_file() -> Path:
    """Path to sample DYM file for testing."""
    file_path = Path(__file__).parent.parent / "data" / "historical_yft_larve.dym"
    if not file_path.exists():
        pytest.skip(f"Sample DYM file not found: {file_path}")
    return file_path


@pytest.fixture
def tmp_dym_file(tmp_path: Path) -> Path:
    """Path to temporary DYM file for writing tests."""
    return tmp_path / "test_output.dym"
