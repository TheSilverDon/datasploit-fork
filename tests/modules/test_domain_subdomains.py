"""Tests for domain.domain_subdomains — subdomain deduplication logic."""

import importlib.util
from pathlib import Path

# Load the module directly to bypass domain/__init__.py's eager import of all siblings
_spec = importlib.util.spec_from_file_location(
    "domain_subdomains",
    Path(__file__).resolve().parent.parent.parent / "domain" / "domain_subdomains.py",
)
domain_subdomains = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(domain_subdomains)
check_and_append_subdomains = domain_subdomains.check_and_append_subdomains


class TestCheckAndAppendSubdomains:
    def test_appends_new_subdomain(self):
        lst = []
        result = check_and_append_subdomains("sub.example.com", lst)
        assert "sub.example.com" in result

    def test_does_not_duplicate(self):
        lst = ["sub.example.com"]
        result = check_and_append_subdomains("sub.example.com", lst)
        assert result.count("sub.example.com") == 1

    def test_appends_multiple_unique(self):
        lst = []
        check_and_append_subdomains("a.example.com", lst)
        check_and_append_subdomains("b.example.com", lst)
        assert len(lst) == 2

    def test_returns_same_list_object(self):
        lst = []
        result = check_and_append_subdomains("x.example.com", lst)
        assert result is lst
