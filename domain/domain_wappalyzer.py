#!/usr/bin/env python

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

from Wappalyzer import Wappalyzer, WebPage
import sys
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Wappalyzer"
REQUIRES = ()

def wappalyzeit(domain):
    temp_list = []
    wappalyzer = Wappalyzer.latest()
    webpage = WebPage.new_from_url(domain)
    set1 = wappalyzer.analyze(webpage)
    if set1:

        for s in set1:
            temp_list.append("\t%s" % s)
        return temp_list
    else:
        return temp_list

def banner():
    return f"Running {MODULE_NAME}"

def main(domain):
    data = {"HTTP": [], "HTTPS": []}
    print("Hitting HTTP and HTTPS:\n")
    try:
        targeturl = "http://" + domain
        data["HTTP"] = wappalyzeit(targeturl)
    except Exception:
        print("[-] HTTP connection was unavailable")
    try:
        targeturl = "https://" + domain
        data["HTTPS"] = wappalyzeit(targeturl)
    except Exception:
        print("[-] HTTPS connection was unavailable")
    return data

def output(data, domain=""):
    for i in data:
        if data[i]:
            print("[+] Third party libraries in Use for %s:" % i)
            for j in data[i]:
                print(j)
        else:
            print("[-] Nothing found for %s. Make sure domain name is passed properly" % i)
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
