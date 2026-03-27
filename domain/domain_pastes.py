#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
    from ..core.google_search import colorize, google_search
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value
    from core.google_search import colorize, google_search

import sys
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Pastes"
REQUIRES = ("google_cse_key", "google_cse_cx")

def banner():
    return f"Running {MODULE_NAME}"

def main(domain):
    if get_config_value('google_cse_key') is not None and get_config_value('google_cse_cx') is not None:
        status, data = google_search(domain)
        return [status, data]
    else:
        return [False, "INVALID_API"]

def output(data, domain=""):
    if not data[0]:
        if isinstance(data, list) and data[1] == "INVALID_API":
            print(colored(style.BOLD + '\n[-] google_cse_key and google_cse_cx not configured. Skipping paste(s) search.\nPlease refer to http://datasploit.readthedocs.io/en/latest/apiGeneration/.\n' + style.END, 'red'))
        else:
            print("Error Message: %s" % data[1]['error']['message'])
            print("Error Code: %s" % data[1]['error']['code'])
            print("Error Description: %s" % data[1]['error']['errors'][0]['reason'])
    else:
        print("[+] %s results found\n" % len(data[1]))
        for x in data[1]:
            title = x.get('title', '')
            snippet = x.get('snippet', '')
            link = x.get('link', '')
            print("Title: %s\nURL: %s\nSnippet: %s\n" % (title, colorize(link), colorize(snippet)))

if __name__ == "__main__":
    try:
        domain = sys.argv[1]
        banner()
        result = main(domain)
        output(result, domain)
    except Exception as e:
        print(e)
        print("Please provide a domain name as argument")
