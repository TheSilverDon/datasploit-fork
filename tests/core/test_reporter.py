"""Tests for core.reporter — JSON and HTML report generation."""

import json
import re
from pathlib import Path

import pytest

from core.result import ModuleResult, ResultStatus
from core.reporter import write_json_report, write_html_report, _build_summary


def _sample_results() -> dict:
    return {
        "domain_whois": ModuleResult(
            module_key="domain_whois", module_name="Domain Whois",
            category="domain", target="example.com",
            status=ResultStatus.SUCCESS,
            data={"registrar": "ACME Inc.", "created": "2000-01-01"},
            duration_s=0.45,
        ),
        "domain_shodan": ModuleResult(
            module_key="domain_shodan", module_name="Domain Shodan",
            category="domain", target="example.com",
            status=ResultStatus.SKIPPED,
            error_msg="missing keys: shodan_api",
            duration_s=0.0,
        ),
        "domain_github": ModuleResult(
            module_key="domain_github", module_name="Domain Github",
            category="domain", target="example.com",
            status=ResultStatus.API_ERROR,
            error_msg="INVALID_API",
            duration_s=0.12,
        ),
    }


class TestBuildSummary:
    def test_counts(self):
        results = _sample_results()
        summary = _build_summary(results)
        assert summary["total"] == 3
        assert summary["success"] == 1
        assert summary["skipped"] == 1
        assert summary["api_error"] == 1
        assert summary["error"] == 0
        assert summary["no_result"] == 0


class TestWriteJsonReport:
    def test_creates_file(self, tmp_path):
        results = _sample_results()
        path = write_json_report(results, "example.com", tmp_path)
        assert path.exists()
        assert path.suffix == ".json"

    def test_valid_json(self, tmp_path):
        results = _sample_results()
        path = write_json_report(results, "example.com", tmp_path)
        payload = json.loads(path.read_text())
        assert payload["target"] == "example.com"
        assert "generated_at" in payload
        assert isinstance(payload["modules"], list)
        assert len(payload["modules"]) == 3

    def test_module_fields(self, tmp_path):
        results = _sample_results()
        path = write_json_report(results, "example.com", tmp_path)
        payload = json.loads(path.read_text())
        whois = next(m for m in payload["modules"] if m["key"] == "domain_whois")
        assert whois["status"] == "success"
        assert whois["duration_s"] == pytest.approx(0.45, abs=0.01)
        assert whois["data"]["registrar"] == "ACME Inc."

    def test_summary_included(self, tmp_path):
        results = _sample_results()
        path = write_json_report(results, "example.com", tmp_path)
        payload = json.loads(path.read_text())
        assert payload["summary"]["total"] == 3
        assert payload["summary"]["success"] == 1


class TestWriteHtmlReport:
    def test_creates_file(self, tmp_path):
        results = _sample_results()
        path = write_html_report(results, "example.com", tmp_path)
        assert path.exists()
        assert path.suffix == ".html"

    def test_html_structure(self, tmp_path):
        results = _sample_results()
        path = write_html_report(results, "example.com", tmp_path)
        html = path.read_text()
        assert "<!DOCTYPE html>" in html
        assert "example.com" in html
        assert "Domain Whois" in html
        assert "Domain Shodan" in html

    def test_status_values_present(self, tmp_path):
        results = _sample_results()
        path = write_html_report(results, "example.com", tmp_path)
        html = path.read_text()
        assert "success" in html
        assert "skipped" in html
        assert "api_error" in html

    def test_no_cdn_links(self, tmp_path):
        """Report must be fully self-contained (no external resources)."""
        results = _sample_results()
        path = write_html_report(results, "example.com", tmp_path)
        html = path.read_text()
        assert "cdn.jsdelivr.net" not in html
        assert "cdnjs.cloudflare.com" not in html
        assert "unpkg.com" not in html
