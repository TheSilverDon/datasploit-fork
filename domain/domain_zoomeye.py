#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value

import requests
import sys
from termcolor import colored
import time

ENABLED = False
MODULE_NAME = "Domain Zoomeye"
REQUIRES = ("zoomeyeuser", "zoomeyepass")
DESCRIPTION = "Disabled: ZoomEye API v2 authentication changed; module needs updating to new endpoint."

def get_accesstoken_zoomeye():
    username = get_config_value('zoomeyeuser')
    password = get_config_value('zoomeyepass')
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    datalogin = '{"username": "%s","password": "%s"}' % (username, password)
    s = requests.post("https://api.zoomeye.org/user/login", data=datalogin, headers=headers)
    try:
        responsedata = s.json()
    except ValueError:
        return False
    if responsedata.get('error') == "bad_request":
        return False
    return responsedata.get('access_token')

def search_zoomeye(domain):
    time.sleep(0.3)
    zoomeye_token = get_accesstoken_zoomeye()
    if not zoomeye_token:
        return False, "BAD_API"
    auth_data = {"Authorization": "JWT " + str(zoomeye_token)}
    req = requests.get('https://api.zoomeye.org/web/search/?query=site:%s&page=1' % domain, headers=auth_data)
    try:
        return True, req.json()
    except ValueError:
        return False, "BAD_RESPONSE"

def banner():
    return f"Running {MODULE_NAME}"

def main(domain):
    if not get_config_value('zoomeyeuser') or not get_config_value('zoomeyepass'):
        return [False, "INVALID_API"]

    success, payload = search_zoomeye(domain)
    if not success:
        return [False, payload]
    return payload

def output(data, domain=""):
    if isinstance(data, list):
        if data[1] == "INVALID_API":
            print(colored(style.BOLD + '\n[-] ZoomEye username and password not configured. Skipping Zoomeye Search.\nPlease refer to http://datasploit.readthedocs.io/en/latest/apiGeneration/.\n' + style.END, 'red'))
        elif data[1] == "BAD_API":
            print(colored(style.BOLD + '\n[-] ZoomEye API is not functional right now.\n' + style.END, 'red'))
        elif data[1] == "BAD_RESPONSE":
            print(colored(style.BOLD + '\n[-] Unexpected response from ZoomEye API.\n' + style.END, 'red'))
        return

    if 'matches' in data:
        print(len(data['matches']))
        for entry in data['matches']:
            if entry['site'].split('.')[-2] == domain.split('.')[-2]:
                if 'title' in entry:
                    print("IP: %s\nSite: %s\nTitle: %s\nHeaders: %s\nLocation: %s\n" % (
                        entry.get('ip', ''),
                        entry.get('site', ''),
                        entry.get('title', ''),
                        entry.get('headers', '').replace("\n\n", ""),
                        entry.get('geoinfo', {})
                    ))
                else:
                    for key, value in entry.items():
                        print("%s: %s" % (key, value))
        print("\n-----------------------------\n")

if __name__ == "__main__":
    domain = sys.argv[1]
    banner()
    result = main(domain)
    if result:
        output(result, domain)
