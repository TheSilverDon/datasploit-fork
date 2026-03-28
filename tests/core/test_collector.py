"""Tests for core.collector — CollectorModule wrapping and ModuleResult."""

import types
import pytest
from core.collector import CollectorModule
from core.result import ResultStatus


def _make_module(name="Test Module", requires=(), enabled=True, main_return=None,
                 output_fn=None, raises=None):
    """Build a minimal fake collector module."""
    mod = types.ModuleType("fake_module")
    mod.MODULE_NAME = name
    mod.REQUIRES = requires
    mod.ENABLED = enabled

    if raises:
        def _main(target):
            raise raises
    else:
        def _main(target):
            return main_return
    mod.main = _main

    mod.output = output_fn or (lambda data, target="": None)
    return mod


class TestCollectorModuleFromModule:
    def test_valid_module(self):
        mod = _make_module()
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        assert cm.key == "test_mod"
        assert cm.name == "Test Module"
        assert cm.enabled is True
        assert cm.requires == ()

    def test_missing_module_name_raises(self):
        mod = types.ModuleType("bad")
        mod.REQUIRES = ()
        with pytest.raises(AttributeError):
            CollectorModule.from_module("bad", "domain", mod)

    def test_requires_must_be_tuple(self):
        mod = types.ModuleType("bad")
        mod.MODULE_NAME = "Bad"
        mod.REQUIRES = ["key"]  # list, not tuple
        with pytest.raises(ValueError):
            CollectorModule.from_module("bad", "domain", mod)

    def test_disabled_module(self):
        mod = _make_module(enabled=False)
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        assert cm.enabled is False


class TestCollectorModuleRun:
    def test_success_result(self, mock_config):
        mod = _make_module(main_return={"key": "val"})
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        result = cm.run("example.com")
        assert result.status == ResultStatus.SUCCESS
        assert result.data == {"key": "val"}
        assert result.duration_s >= 0

    def test_no_result_when_empty(self, mock_config):
        mod = _make_module(main_return={})
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        result = cm.run("example.com")
        assert result.status == ResultStatus.NO_RESULT

    def test_error_result_on_exception(self, mock_config):
        mod = _make_module(raises=RuntimeError("boom"))
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        result = cm.run("example.com")
        assert result.status == ResultStatus.ERROR
        assert "boom" in result.error_msg

    def test_api_error_on_legacy_sentinel(self, mock_config):
        mod = _make_module(main_return=[False, "INVALID_API"])
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        result = cm.run("example.com")
        assert result.status == ResultStatus.API_ERROR
        assert "INVALID_API" in result.error_msg

    def test_missing_prerequisites(self, no_config):
        mod = _make_module(requires=("some_api_key",))
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        missing = cm.missing_prerequisites()
        assert "some_api_key" in missing

    def test_no_missing_prerequisites_when_config_present(self, mock_config):
        mod = _make_module(requires=("some_api_key",))
        cm = CollectorModule.from_module("test_mod", "domain", mod)
        missing = cm.missing_prerequisites()
        assert missing == ()
