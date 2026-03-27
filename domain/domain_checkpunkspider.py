#!/usr/bin/env python

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

import requests
import sys
import warnings
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Punkspider"
REQUIRES = ()

warnings.filterwarnings("ignore")

def checkpunkspider(reversed_domain):
    req = requests.post("http://www.punkspider.org/service/search/detail/" + reversed_domain)
    try:
        return req.json()
    except ValueError:
        return {}

def banner():
    return f"Running {MODULE_NAME}"

def main(domain):
    reversed_domain = ""
    for x in reversed(domain.split(".")):
        reversed_domain = reversed_domain + "." + x
    reversed_domain = reversed_domain[1:]
    return checkpunkspider(reversed_domain)

def output(data, domain=""):
    if data is not None:
        if 'data' in data and len(data['data']) >= 1:
            print(colored("Few vulnerabilities found at Punkspider", 'green'))
            for x in data['data']:
                print("==> ", x['bugType'])
                print("Method:", x['verb'].upper())
                print("URL:\n" + x['vulnerabilityUrl'])
                print("Param:", x['parameter'])
        else:
            print(colored("[-] No Vulnerabilities found on PunkSpider\n", 'red'))

if __name__ == "__main__":
    try:
        domain = sys.argv[1]
        banner()
        result = main(domain)
        output(result, domain)
    except Exception as e:
        print(e)
        print("Please provide a domain name as argument")
