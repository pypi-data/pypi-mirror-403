"""Pytest configuration for tasks tests."""

import pytest


# Configure pytest-asyncio to auto-mode
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
