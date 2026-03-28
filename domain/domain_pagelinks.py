#!/usr/bin/env python

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

import sys
import requests
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Page Links"
REQUIRES = ()

def pagelinks(domain):
    try:
        req = requests.get('http://api.hackertarget.com/pagelinks/?q=%s' % domain)
        page_links = req.text.splitlines()
        return page_links
    except requests.RequestException:
        print('Connection time out.')
        return []

def banner():
    return f"Running {MODULE_NAME}"

def main(domain):
    return pagelinks(domain)

def output(data, domain=""):
    for x in data:
        print(x)
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
