"""Shared pytest fixtures for Facet tests."""

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path
