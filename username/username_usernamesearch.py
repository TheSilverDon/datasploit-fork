#!/usr/bin/env python

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

import sys
import requests
from bs4 import BeautifulSoup
from termcolor import colored

# Control whether the module is enabled or not
ENABLED = True
MODULE_NAME = "Username Username Search"
REQUIRES = ()

def banner():
    return f"Running {MODULE_NAME}"

def main(username):
    data = {"username": username}
    req = requests.post('https://usersearch.org/results_normal.php', data=data)
    soup = BeautifulSoup(req.text, "html.parser")
    atag = soup.findAll('a', {'class': 'pretty-button results-button'})
    profiles = []
    for at in atag:
        if at.text == "View Profile":
            profiles.append(at['href'])
    return profiles

def output(data, username=""):
    for lnk in data:
        print(lnk)
    print("\n-----------------------------\n")

if __name__ == "__main__":
    try:
        username = sys.argv[1]
        banner()
        result = main(username)
        output(result, username)
    except Exception as e:
        print(e)
        print("Please provide a username as argument")
