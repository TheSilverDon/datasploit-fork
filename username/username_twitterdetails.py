#!/usr/bin/env python

try:
    from ..core.style import style
    from ..core.config import get_config_value
except ImportError:  # pragma: no cover - legacy script execution
    from core.style import style
    from core.config import get_config_value

import os
import re
import sys
import tempfile
import tweepy
import requests
from collections import Counter
from termcolor import colored

# Control whether the module is enabled or not
ENABLED = True
MODULE_NAME = "Username Twitter Details"
REQUIRES = (
    "twitter_consumer_key",
    "twitter_consumer_secret",
    "twitter_access_token",
    "twitter_access_token_secret",
)

def banner():
    return f"Running {MODULE_NAME}"

def twitterdetails(username):
    twitter_consumer_key = get_config_value('twitter_consumer_key')
    twitter_consumer_secret = get_config_value('twitter_consumer_secret')
    twitter_access_token = get_config_value('twitter_access_token')
    twitter_access_token_secret = get_config_value('twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)
    userdetails = {}
    activitydetails = {}
    try:
        userinfo = api.get_user(screen_name=username)
    except Exception as e:
        api_code = getattr(e, 'api_code', None)
        message = str(e)
        if hasattr(e, 'message') and isinstance(e.message, list) and e.message:
            api_code = e.message[0].get('code')
            message = e.message[0].get('message')
        if api_code == 63:
            print(colored(style.BOLD + '[!] Error: ' + str(message) + style.END, 'red'))
        return activitydetails, userdetails

    userdetails['Followers'] = userinfo.followers_count
    userdetails['Following'] = userinfo.friends_count
    userdetails['Geolocation Enabled'] = userinfo.geo_enabled
    try:
        userdetails['Homepage'] = userinfo.entities['url']['urls'][0]['display_url']
    except KeyError:
        pass
    userdetails['Language'] = userinfo.lang
    userdetails['Number of Tweets'] = userinfo.statuses_count
    userdetails['Profile Description'] = userinfo.description
    userdetails['Profile Set Location'] = userinfo.location
    userdetails['Time Zone'] = userinfo.time_zone
    userdetails['User ID'] = userinfo.id
    userdetails['UTC Offset'] = userinfo.utc_offset
    userdetails['Verified Account'] = userinfo.verified

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as f:
        tmp_path = f.name
        for tweet in tweepy.Cursor(api.user_timeline, id=username).items(1000):
            f.write(tweet.text + "\n")

    with open(tmp_path, 'r', encoding='utf-8') as f:
        q = f.read()
    strings = re.findall(r'(?:\#+[\w_]+[\w\'_\-]*[\w_]+)', q)
    tusers = re.findall(r'(?:@[\w_]+)', q)
    os.remove(tmp_path)

    hashlist = [item.strip('#').lower() for item in strings]
    userlist = [itm.strip('@').lower() for itm in tusers]

    activitydetails = {
        'Hashtag Interactions': hashlist[:10],
        'User Interactions': userlist[:10]
    }

    return activitydetails, userdetails

def main(username):
    twitter_consumer_key = get_config_value('twitter_consumer_key')
    twitter_consumer_secret = get_config_value('twitter_consumer_secret')
    twitter_access_token = get_config_value('twitter_access_token')
    twitter_access_token_secret = get_config_value('twitter_access_token_secret')

    if (twitter_consumer_key is not None and twitter_consumer_secret is not None and
            twitter_access_token is not None and twitter_access_token_secret is not None):
        r = requests.get("https://twitter.com/%s" % username)
        if r.status_code == 200:
            activitydetails, userdetails = twitterdetails(username)
            return [activitydetails, userdetails]
        else:
            return None
    else:
        return [False, "INVALID_API"]

def output(data, username=""):
    if data[1] == "INVALID_API":
        print(colored(f"{style.BOLD}\n[-] Twitter API Keys not configured. Skipping Twitter search.\nPlease refer to http://datasploit.readthedocs.io/en/latest/apiGeneration/.\n{style.END}", "red"))
    else:
        if data and data[0]:
            hashlist = data[0]['Hashtag Interactions']
            userlist = data[0]['User Interactions']
            userdetails = data[1]
            for k, v in userdetails.items():
                try:
                    print(k + ": " + str(v))
                except UnicodeEncodeError as e:
                    print(colored(style.BOLD + '[!] Error: ' + str(e) + style.END, 'red'))
            print("\n")
            count = Counter(hashlist).most_common()
            print("Top Hashtag Occurrence for user " + username + " based on last 1000 tweets")
            for hash_value, cnt in count:
                print("#" + hash_value + " : " + str(cnt))
            print("\n")

            countu = Counter(userlist).most_common()
            print("Top User Occurrence for user " + username + " based on last 1000 tweets")
            for usr, cnt in countu:
                print("@" + usr + " : " + str(cnt))
        else:
            print("No Associated Twitter account found.")

if __name__ == "__main__":
    try:
        username = sys.argv[1]
        banner()
        result = main(username)
        output(result, username)
    except Exception as e:
        print(e)
        print("Please provide a username as argument")
