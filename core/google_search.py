"""Shared Google Custom Search Engine utilities used by paste modules."""

import re
import requests

try:
    from .config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.config import get_config_value


def colorize(string):
    colourFormat = '\033[{0}m'
    colourStr = colourFormat.format(32)
    resetStr = colourFormat.format(0)
    lastMatch = 0
    formattedText = ''
    for match in re.finditer(
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,4})|/(?:http:\/\/)?(?:([^.]+)\.)?datasploit\.info/|/(?:http:\/\/)?(?:([^.]+)\.)?(?:([^.]+)\.)?datasploit\.info/)',
            string):
        start, end = match.span()
        formattedText += string[lastMatch: start]
        formattedText += colourStr
        formattedText += string[start: end]
        formattedText += resetStr
        lastMatch = end
    formattedText += string[lastMatch:]
    return formattedText


def google_search(query):
    google_cse_key = get_config_value('google_cse_key')
    google_cse_cx = get_config_value('google_cse_cx')
    url = "https://www.googleapis.com/customsearch/v1?key=%s&cx=%s&q=\"%s\"&start=1" % (
        google_cse_key, google_cse_cx, query)
    all_results = []
    r = requests.get(url, headers={'referer': 'www.datasploit.info/hello'})
    data = r.json()
    if 'error' in data:
        return False, data
    if int(data['searchInformation']['totalResults']) > 0:
        all_results += data['items']
        while "nextPage" in data['queries']:
            next_index = data['queries']['nextPage'][0]['startIndex']
            url = "https://www.googleapis.com/customsearch/v1?key=%s&cx=%s&q=\"%s\"&start=%s" % (
                google_cse_key, google_cse_cx, query, next_index)
            data = requests.get(url).json()
            if 'error' in data:
                return True, all_results
            else:
                all_results += data['items']
    return True, all_results
