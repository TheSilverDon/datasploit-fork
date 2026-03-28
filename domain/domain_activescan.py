#!/usr/bin/env python
"""Active subdomain takeover scanner.

For each subdomain discovered by the Domain Subdomains module, this
collector checks whether a dangling CNAME record exists and whether the
HTTP/S endpoint returns a 403 or 404 that may indicate a sub-domain
takeover opportunity.
"""

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

import sys
import requests
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Active Scan"
REQUIRES = ()
DESCRIPTION = (
    "Probes discovered subdomains for dangling CNAME records that may be "
    "vulnerable to subdomain takeover (HTTP 403/404 on a live CNAME)."
)


def banner():
    return f"Running {MODULE_NAME}"


def main(domain):
    try:
        from . import domain_subdomains, domain_dnsrecords
    except ImportError:
        from domain import domain_subdomains, domain_dnsrecords

    subdomains = domain_subdomains.main(domain)
    results = {"vulnerable": [], "accessible": [], "no_cname": []}

    for sub in subdomains:
        cname = domain_dnsrecords.fetch_dns_records(sub, "CNAME")
        if not isinstance(cname, list):
            results["no_cname"].append(sub)
            continue
        # Sub has a CNAME — check if the endpoint is reachable
        for scheme in ("http", "https"):
            try:
                r = requests.get(f"{scheme}://{sub}", timeout=5)
                if r.status_code in (403, 404):
                    results["vulnerable"].append({
                        "subdomain": sub,
                        "cname": cname,
                        "scheme": scheme,
                        "status_code": r.status_code,
                    })
                else:
                    results["accessible"].append({"subdomain": sub, "scheme": scheme,
                                                   "status_code": r.status_code})
                break  # no need to try https if http succeeded
            except requests.RequestException:
                continue

    return results


def output(data, domain=""):
    if not data:
        print(colored("[-] No subdomain data to scan.", "yellow"))
        return

    vulnerable = data.get("vulnerable", [])
    accessible = data.get("accessible", [])

    if vulnerable:
        print(colored(f"\n[!] {len(vulnerable)} potentially vulnerable subdomains found:\n", "red"))
        for entry in vulnerable:
            print(f"  {entry['subdomain']}  CNAME→{entry['cname']}  [{entry['scheme'].upper()} {entry['status_code']}]")
    else:
        print(colored("\n[+] No subdomain takeover candidates detected.", "green"))

    if accessible:
        print(colored(f"\n[+] {len(accessible)} accessible subdomains:", "green"))
        for entry in accessible:
            print(f"  {entry['subdomain']}  [{entry['scheme'].upper()} {entry['status_code']}]")

    print("\n-----------------------------\n")


if __name__ == "__main__":
    try:
        domain = sys.argv[1]
        banner()
        result = main(domain)
        output(result, domain)
    except Exception as e:
        print(e)
        print("Please provide a domain name as argument")
