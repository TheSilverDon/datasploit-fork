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
MODULE_NAME = "Email Pastes"
REQUIRES = ("google_cse_key", "google_cse_cx")

def banner():
    return f"Running {MODULE_NAME}"

def main(email):
    if get_config_value('google_cse_key') is not None and get_config_value('google_cse_cx') is not None:
        status, data = google_search(email)
        return [status, data]
    else:
        return [False, "INVALID_API"]

def output(data, email):
    if not data[0]:
        if isinstance(data[1], str) and data[1] == "INVALID_API":
            print(colored(style.BOLD + '[-] google_cse_key and google_cse_cx not configured. Skipping paste(s) search.\nPlease refer to http://datasploit.readthedocs.io/en/latest/apiGeneration/.\n' + style.END, 'red'))
        elif isinstance(data[1], dict) and 'error' in data[1]:
            print("Error Message: %s" % data[1]['error'].get('message', ''))
            print("Error Code: %s" % data[1]['error'].get('code', ''))
            errors = data[1]['error'].get('errors', [])
            if errors:
                print("Error Description: %s" % errors[0].get('reason', ''))
        return
    else:
        #print(data[0])
        print("[+] %s results found\n" % len(data[1]))
        for x in data[1]:
            title = x.get('title', '')
            snippet = x.get('snippet', '')
            link = x.get('link', '')
            print("Title: %s\nURL: %s\nSnippet: %s\n" % (title, colorize(link), colorize(snippet)))

if __name__ == "__main__":
    try:
        email = sys.argv[1]
        banner()
        result = main(email)
        output(result, email)
    except Exception as e:
        print(e)
