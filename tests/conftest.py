"""Shared pytest fixtures for DataSploit tests."""

import pytest


@pytest.fixture
def mock_config(monkeypatch):
    """Provide a predictable config that does not read from disk or env vars."""
    monkeypatch.setattr(
        "core.config.get_config_value",
        lambda key: f"test_value_for_{key}",
    )
    monkeypatch.setattr(
        "core.collector.get_config_value",
        lambda key: f"test_value_for_{key}",
    )
    # Also clear the lru_cache so load_config() doesn't return stale data
    from core.config import load_config
    load_config.cache_clear()
    yield
    load_config.cache_clear()


@pytest.fixture
def no_config(monkeypatch):
    """Simulate a missing config file (all keys return None)."""
    monkeypatch.setattr("core.config.get_config_value", lambda key: None)
    monkeypatch.setattr("core.collector.get_config_value", lambda key: None)
    from core.config import load_config
    load_config.cache_clear()
    yield
    load_config.cache_clear()
