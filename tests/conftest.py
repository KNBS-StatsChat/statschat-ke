"""Shared pytest fixtures for the test suite."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Force AnyIO to use asyncio to avoid optional trio dependency."""
    return "asyncio"
