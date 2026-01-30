"""Pytest configuration and fixtures."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def purge_actual_folder():
    """Purge the actual/ folder before running any tests."""
    actual_dir = Path(__file__).parent / "fixtures" / "actual"
    if actual_dir.exists():
        shutil.rmtree(actual_dir)
    actual_dir.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def actual_path(request):
    """
    Provide a path under tests/fixtures/actual/ for test outputs.

    Creates a unique subdirectory for each test to avoid conflicts.
    """
    base_dir = Path(__file__).parent / "fixtures" / "actual"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectory using test name
    test_dir = base_dir / request.node.name
    test_dir.mkdir(parents=True, exist_ok=True)

    return test_dir
