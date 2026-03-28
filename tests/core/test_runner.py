"""Tests for core.runner — concurrent execution and result aggregation."""

import types
import pytest
from core.collector import CollectorModule
from core.registry import CollectorRegistry
from core.runner import CollectorRunner
from core.result import ResultStatus
from core.types import TargetType


def _make_collector(key, name, enabled=True, requires=(), main_return={"data": 1}):
    mod = types.ModuleType(key)
    mod.MODULE_NAME = name
    mod.REQUIRES = requires
    mod.ENABLED = enabled
    mod.main = lambda target: main_return
    mod.output = lambda data, target="": None
    mod.banner = lambda: f"Running {name}"
    return CollectorModule.from_module(key, "domain", mod)


class _MockRegistry:
    def __init__(self, collectors):
        self._collectors = collectors

    def get_collectors(self, category):
        return self._collectors


class TestCollectorRunner:
    def test_returns_dict_of_results(self, mock_config):
        collectors = [_make_collector("mod_a", "Mod A"), _make_collector("mod_b", "Mod B")]
        registry = _MockRegistry(collectors)
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert "mod_a" in results
        assert "mod_b" in results

    def test_successful_results(self, mock_config):
        collectors = [_make_collector("mod_a", "Mod A", main_return={"found": True})]
        registry = _MockRegistry(collectors)
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert results["mod_a"].status == ResultStatus.SUCCESS
        assert results["mod_a"].data == {"found": True}

    def test_disabled_collector_is_skipped(self, mock_config):
        collectors = [_make_collector("mod_a", "Mod A", enabled=False)]
        registry = _MockRegistry(collectors)
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert results["mod_a"].status == ResultStatus.SKIPPED

    def test_missing_prereq_collector_is_skipped(self, no_config):
        collectors = [_make_collector("mod_a", "Mod A", requires=("secret_key",))]
        registry = _MockRegistry(collectors)
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert results["mod_a"].status == ResultStatus.SKIPPED

    def test_empty_registry_returns_empty_dict(self, mock_config):
        registry = _MockRegistry([])
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert results == {}

    def test_multiple_collectors_all_run(self, mock_config):
        collectors = [_make_collector(f"mod_{i}", f"Mod {i}") for i in range(5)]
        registry = _MockRegistry(collectors)
        runner = CollectorRunner(registry=registry)
        results = runner.run(TargetType.DOMAIN, "example.com")
        assert len(results) == 5
        for key, result in results.items():
            assert result.status == ResultStatus.SUCCESS
