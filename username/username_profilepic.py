#!/usr/bin/env python

try:
    from ..core.style import style
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style

import os
import sys
import requests
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
from bs4 import BeautifulSoup
from . import username_usernamesearch
from termcolor import colored

# Control whether the module is enabled or not
ENABLED = True
MODULE_NAME = "Username Profile Pic"
REQUIRES = ()

def extracting(imglinks, username, prourl, tag, attribute, value, finattrib, profile):
    res = requests.get(prourl)
    soup = BeautifulSoup(res.text, "lxml")
    img = soup.find(tag, {attribute: value})
    if img is None:
        return imglinks

    img_url = img.get(finattrib)
    if not img_url:
        return imglinks

    if profile == "ask.fm" and not img_url.startswith("http"):
        img_url = "http:" + img_url

    imglinks.append(img_url)
    base = Path("profile_pic").resolve()
    path = (base / username / (profile + ".jpg")).resolve()
    if not str(path).startswith(str(base)):
        return imglinks
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(img_url, str(path))
    return imglinks

def profilepic(urls, username):
    imagelinks = []
    for url in urls:
        if 'etsy' in url:
            try:
                tg = 'meta'
                att = 'property'
                val = 'og:image'
                valx = 'content'
                pro = "etsy"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'gravatar' in url:
            try:
                tg = 'a'
                att = 'class'
                val = 'photo-0'
                valx = 'href'
                pro = "gravatar"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'youtube' in url:
            try:
                tg = 'link'
                att = 'itemprop'
                val = 'thumbnailUrl'
                valx = 'href'
                pro = "youtube"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'twitter' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'ProfileAvatar-image'
                valx = 'src'
                pro = "twitter"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                global twitterex
                twitterex = 1
                continue
            except KeyError:
                pass
        elif 'photobucket' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'avatar smallProfile'
                valx = 'src'
                pro = "photobucket"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'pinterest' in url:
            try:
                tg = 'meta'
                att = 'property'
                val = 'og:image'
                valx = 'content'
                pro = "pinterest"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'ebay' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'prof_img img'
                valx = 'src'
                pro = "ebay"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'steam' in url:
            try:
                tg = 'link'
                att = 'rel'
                val = 'image_src'
                valx = 'href'
                pro = "steam"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'deviantart' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'avatar float-left'
                valx = 'src'
                pro = "deviantart"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'last.fm' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'avatar'
                valx = 'src'
                pro = "last.fm"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'vimeo' in url:
            try:
                tg = 'meta'
                att = 'property'
                val = 'og:image'
                valx = 'content'
                pro = "vimeo"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'ask.fm' in url:
            try:
                tg = 'meta'
                att = 'property'
                val = 'og:image'
                valx = 'content'
                pro = "ask.fm"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'tripadvisor' in url:
            try:
                tg = 'img'
                att = 'class'
                val = 'avatarUrl'
                valx = 'src'
                pro = "tripadvisor"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
        elif 'tumblr' in url:
            try:
                tg = 'link'
                att = 'rel'
                val = 'icon'
                valx = 'href'
                pro = "tumblr"
                imagelinks = extracting(imagelinks, username, url, tg, att, val, valx, pro)
                continue
            except KeyError:
                pass
    return imagelinks

def banner():
    return f"Running {MODULE_NAME}"

def main(username):
    usernames = username_usernamesearch.main(username)
    file_path = "profile_pic/%s" % username
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    imagelinks = profilepic(usernames, username)
    print("Profile Pics saved to : %s" % file_path)
    return imagelinks

def output(data, username=""):
    for link in data:
        print(link)

if __name__ == "__main__":
    #try:
    username = sys.argv[1]
    banner()
    result = main(username)
    output(result, username)
    '''
    except Exception as e:
        print(e)
        print("Please provide a username as argument")
    '''
