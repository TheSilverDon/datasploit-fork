#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value

import re, sys, json, time, requests
from termcolor import colored

ENABLED = True
MODULE_NAME = "Domain Censys"
REQUIRES = ("censysio_id", "censysio_secret")

def censys_search(domain):
    censys_list = []

    pages = float('inf')
    page = 1

    censysio_id = get_config_value('censysio_id')
    censysio_secret = get_config_value('censysio_secret')

    while page <= pages:
        print("Parsed and collected results from page %s" % str(page))
        #time.sleep(0.5)
        params = {'query': domain, 'page': page}
        res = requests.post("https://www.censys.io/api/v1/search/ipv4", json=params,
                            auth=(censysio_id, censysio_secret))
        payload = res.json()

        if 'error' not in payload:
            if 'results' in payload:
                for r in payload['results']:
                    temp_dict = {}
                    ip = r["ip"]
                    proto = r["protocols"]
                    proto = [p.split("/")[0] for p in proto]
                    proto.sort(key=float)
                    protoList = ','.join(map(str, proto))

                    temp_dict["ip"] = ip
                    temp_dict["protocols"] = protoList

                    if '80' in protoList:
                        new_dict = view(ip, temp_dict)
                        censys_list.append(new_dict)
                    else:
                        censys_list.append(temp_dict)

                    pages = payload['metadata']['pages']
                    page += 1
        else:
            censys_list = None
            break
    return censys_list

def view(server, temp_dict):
    censysio_id = get_config_value('censysio_id')
    censysio_secret = get_config_value('censysio_secret')
    res = requests.get("https://www.censys.io/api/v1/view/ipv4/%s" % (server),
                       auth=(censysio_id, censysio_secret))
    payload = res.json()

    http_get = payload.get('80', {}).get('http', {}).get('get', {})
    title = http_get.get('title')
    if title:
        temp_dict['title'] = title
    server = http_get.get('headers', {}).get('server')
    if server:
        temp_dict['server_header'] = server
    return temp_dict

def output(data, domain=""):
    if data is not None:
        for i in data:
            print(i)

def main(domain):
    data = censys_search(domain)
    return data

if __name__ == "__main__":
    try:
        domain = sys.argv[1]
        result = main(domain)
        output(result, domain)
    except Exception as e:
        print(e)
        print(colored(style.BOLD + '\n[-] Please provide a domain name as argument\n' + style.END, 'red'))
