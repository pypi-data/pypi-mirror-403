"""Shared test fixtures for tdd-llm."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Set NO_COLOR before any imports to disable Rich colors
os.environ["NO_COLOR"] = "1"


def pytest_configure(config):
    """Set environment variables before test collection."""
    os.environ["NO_COLOR"] = "1"


@pytest.fixture(autouse=True)
def skip_first_run_wizard():
    """Disable first-run wizard for all tests."""
    with mock.patch("tdd_llm.cli.is_first_run", return_value=False):
        yield


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dirpath = tempfile.mkdtemp()
    yield Path(dirpath)
    shutil.rmtree(dirpath)


@pytest.fixture
def temp_config_file(temp_dir):
    """Create a temporary config file path."""
    return temp_dir / "config.yaml"
