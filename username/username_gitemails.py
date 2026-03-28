#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value

import sys
import requests
from termcolor import colored
from collections import Counter

# Control whether the module is enabled or not
ENABLED = True
WRITE_TEXT_FILE = True
MODULE_NAME = "GitHub Emails"
REQUIRES = ("github_access_token",)

GITHUB_BASE = "https://api.github.com"
access_token = get_config_value('github_access_token')

def __boldtext(text, color='blue'):
    BOLD = '\033[1m'
    END = '\033[0m'
    return colored(BOLD + text + END, color)

def banner():
    return f"Running {MODULE_NAME}"

def __get_username_repos(username):
    r = requests.get("%s/users/%s/repos" % (GITHUB_BASE, username),
                     headers={"Authorization": f"token {access_token}"})
    repos = []
    response = r.json()
    if "message" in response:
        return []
    else:
        for repo in response:
            repos.append(repo['full_name'])
    return repos

def __get_email_from_repo(repo, username):
    r = requests.get("%s/repos/%s/commits" % (GITHUB_BASE, repo),
                     headers={"Authorization": f"token {access_token}"})
    response = r.json()
    emails = []
    if isinstance(response, list):
        for commit in response:
            got_email = commit['commit']['committer']['email']
            if not got_email == "noreply@github.com":
                emails.append(commit['commit']['committer']['email'])
    return emails

def main(username):
    # Use the username variable to do some stuff and return the data
    repos = __get_username_repos(username)
    main_emails_list = []
    for repo in repos:
        main_emails_list += __get_email_from_repo(repo, username)
    main_emails_list = [s[0] for s in Counter(main_emails_list).most_common()]
    return main_emails_list

def output(data, username=""):
    # Use the data variable to print(out to console as you like)
    if data:
        for i in data:
            print(i)
    else:
        print(colored("Found nothing!", "red"))

def output_text(data):
    return "\n".join(data)

if __name__ == "__main__":
    try:
        username = sys.argv[1]
        banner()
        result = main(username)
        output(result, username)
    except Exception as e:
        print(e)
        print("Please provide a username as argument")
