"""Tests for core.result — ModuleResult and ResultStatus."""

import pytest
from core.result import ModuleResult, ResultStatus


def _make_result(**kwargs):
    defaults = dict(
        module_key="test_module",
        module_name="Test Module",
        category="domain",
        target="example.com",
        status=ResultStatus.SUCCESS,
    )
    defaults.update(kwargs)
    return ModuleResult(**defaults)


class TestResultStatus:
    def test_all_statuses_have_string_values(self):
        for status in ResultStatus:
            assert isinstance(status.value, str)
            assert status.value  # non-empty

    def test_status_values(self):
        assert ResultStatus.SUCCESS.value == "success"
        assert ResultStatus.NO_RESULT.value == "no_result"
        assert ResultStatus.SKIPPED.value == "skipped"
        assert ResultStatus.API_ERROR.value == "api_error"
        assert ResultStatus.ERROR.value == "error"


class TestModuleResult:
    def test_basic_construction(self):
        r = _make_result()
        assert r.module_key == "test_module"
        assert r.module_name == "Test Module"
        assert r.category == "domain"
        assert r.target == "example.com"
        assert r.status == ResultStatus.SUCCESS

    def test_defaults(self):
        r = _make_result()
        assert r.data is None
        assert r.error_msg == ""
        assert r.duration_s == 0.0

    def test_with_data(self):
        data = {"key": "value"}
        r = _make_result(data=data)
        assert r.data == data

    def test_error_result(self):
        r = _make_result(status=ResultStatus.ERROR, error_msg="Connection refused")
        assert r.status == ResultStatus.ERROR
        assert r.error_msg == "Connection refused"

    def test_duration(self):
        r = _make_result(duration_s=1.23)
        assert r.duration_s == pytest.approx(1.23)

    def test_skipped_result(self):
        r = _make_result(status=ResultStatus.SKIPPED, error_msg="missing keys: api_key")
        assert r.status == ResultStatus.SKIPPED
        assert "api_key" in r.error_msg
