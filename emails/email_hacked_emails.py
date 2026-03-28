#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value

import sys
import requests
try:
    import cfscrape
except Exception:
    cfscrape = None
from termcolor import colored

# Control whether the module is enabled or not
ENABLED = False
MODULE_NAME = "Email Hacked Emails"
REQUIRES = ()
DESCRIPTION = "Disabled: Source endpoint no longer publicly available."

def banner():
    return f"Running {MODULE_NAME}"

def main(email):
    req = requests.get("https://hacked-emails.com/api?q=%s" % email)
    if "jschl-answer" in req.text:
        if cfscrape is None:
            print("Cloudflare protection detected but cfscrape is unavailable. Skipping.")
            return {}
        print("Cloudflare detected... Solving challenge.")
        scraper = cfscrape.create_scraper()
        req = scraper.get("https://hacked-emails.com/api?q=%s" % email)
        print(req.text)
        if "jschl-answer" in req.text:
            return {}
    try:
        return req.json()
    except ValueError:
        return {}

def output(data, email=""):
    # Use the data variable to print(out to console as you like)
    if data.get('status') == 'found':
        print("%s Results found" % data.get('results'))
        for rec in data.get('data'):
            print("------")
            print(colored(style.BOLD + 'Leak Title: ' + style.END) + str(rec.get('title')))
            print(colored(style.BOLD + 'Details: ' + style.END) + str(rec.get('details')))
            if rec.get('source_url') == "#":
                rec['source_url'] = "N/A"
            print(colored(style.BOLD + 'Leak URL: ' + style.END) + str(rec.get('source_url')))
            print(colored(style.BOLD + 'Leaked on: ' + style.END) + str(rec.get('date_created')))
            if rec.get('source_provider') == 'anon':
                rec['source_provider'] = "Anonymous"
            print(colored(style.BOLD + 'Source: ' + style.END) + str(rec.get('source_provider')))
    else:
        print("[-] No Data Found")

if __name__ == "__main__":
    try:
        email = sys.argv[1]
        banner()
        result = main(email)
        output(result, email)
    except Exception as e:
        print(e)
        print("Please provide an email as argument")
