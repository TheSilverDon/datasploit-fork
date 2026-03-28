"""Tests for domain.domain_dnsrecords — DNS record fetching."""

import importlib.util
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import dns.resolver

# Load the module directly to bypass domain/__init__.py's eager import of all siblings
_spec = importlib.util.spec_from_file_location(
    "domain_dnsrecords",
    Path(__file__).resolve().parent.parent.parent / "domain" / "domain_dnsrecords.py",
)
domain_dnsrecords = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(domain_dnsrecords)
fetch_dns_records = domain_dnsrecords.fetch_dns_records
parse_dns_records = domain_dnsrecords.parse_dns_records


class TestFetchDnsRecords:
    def test_returns_list_on_success(self):
        mock_answer = MagicMock()
        mock_rdata = MagicMock()
        mock_rdata.__str__ = lambda self: "1.2.3.4"
        mock_answer.__iter__ = lambda self: iter([mock_rdata])

        with patch.object(domain_dnsrecords.dns.resolver, "resolve", return_value=mock_answer):
            result = fetch_dns_records("example.com", "A")

        assert isinstance(result, list)
        assert result == ["1.2.3.4"]

    def test_returns_colored_string_on_nxdomain(self):
        with patch.object(domain_dnsrecords.dns.resolver, "resolve",
                          side_effect=dns.resolver.NXDOMAIN):
            result = fetch_dns_records("nonexistent.example.com", "A")
        assert "No Records Found" in result

    def test_returns_colored_string_on_no_answer(self):
        with patch.object(domain_dnsrecords.dns.resolver, "resolve",
                          side_effect=dns.resolver.NoAnswer):
            result = fetch_dns_records("example.com", "AAAA")
        assert "No Records Found" in result

    def test_returns_colored_string_on_no_nameservers(self):
        with patch.object(domain_dnsrecords.dns.resolver, "resolve",
                          side_effect=dns.resolver.NoNameservers):
            result = fetch_dns_records("example.com", "MX")
        assert "No Records Found" in result


class TestParseDnsRecords:
    def test_returns_dict_with_all_record_types(self):
        with patch.object(domain_dnsrecords, "fetch_dns_records", return_value=["1.2.3.4"]):
            result = parse_dns_records("example.com")

        expected_keys = {
            "SOA Records", "MX Records", "TXT Records", "A Records",
            "Name Server Records", "CNAME Records", "AAAA Records",
        }
        assert set(result.keys()) == expected_keys

    def test_values_are_from_fetch(self):
        with patch.object(domain_dnsrecords, "fetch_dns_records", return_value=["ns1.example.com"]):
            result = parse_dns_records("example.com")
        for v in result.values():
            assert v == ["ns1.example.com"]
