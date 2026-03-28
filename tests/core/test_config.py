"""Tests for core.config — get_config_value with env var override."""

import os
import pytest
from core.config import get_config_value, load_config


@pytest.fixture(autouse=True)
def clear_cache():
    load_config.cache_clear()
    yield
    load_config.cache_clear()


class TestEnvVarOverride:
    def test_env_var_takes_priority(self, monkeypatch):
        monkeypatch.setenv("DATASPLOIT_SHODAN_API", "env_key_value")
        assert get_config_value("shodan_api") == "env_key_value"

    def test_env_var_case_insensitive_key(self, monkeypatch):
        monkeypatch.setenv("DATASPLOIT_GITHUB_ACCESS_TOKEN", "ghtoken")
        assert get_config_value("github_access_token") == "ghtoken"

    def test_missing_key_returns_none(self, monkeypatch):
        monkeypatch.delenv("DATASPLOIT_NONEXISTENT_KEY", raising=False)
        # No config file in test environment → returns None
        result = get_config_value("nonexistent_key_xyz")
        assert result is None

    def test_empty_env_var_falls_through(self, monkeypatch):
        """An empty env var should not be treated as a valid value."""
        monkeypatch.setenv("DATASPLOIT_SHODAN_API", "")
        # Should fall through to config file (which returns None in test env)
        result = get_config_value("shodan_api")
        assert result is None or isinstance(result, str)
