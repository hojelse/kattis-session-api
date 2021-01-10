#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import re
import sys
from requests_html import HTMLSession

import requests
import requests.exceptions
import configparser

# End Python 2/3 compatibility

_DEFAULT_CONFIG = '/usr/local/etc/kattisrc'

_HEADERS = {'User-Agent': 'kattis-session-api'}


class ConfigError(Exception):
    pass

def get_config():
    """Returns a ConfigParser object for the .kattisrc file(s)
    """
    cfg = configparser.ConfigParser()
    if os.path.exists(_DEFAULT_CONFIG):
        cfg.read(_DEFAULT_CONFIG)

    if not cfg.read([os.path.join(os.path.expanduser("~"), '.kattisrc'),
                     os.path.join(os.path.dirname(sys.argv[0]), '.kattisrc')]):
        raise ConfigError('''\
I failed to read in a config file from your home directory or from the
same directory as this script. To download a .kattisrc file please visit
https://<kattis>/download/kattisrc

The file should look something like this:
[user]
username: yourusername
token: *********

[kattis]
hostname: <kattis>
loginurl: https://<kattis>/login
submissionurl: https://<kattis>/submit
submissionsurl: https://<kattis>/submissions''')
    return cfg

def login_from_config(cfg):
    """Log in to Kattis using the access information in a kattisrc file

    Returns a requests.Response with cookies needed to be able to submit
    """
    username = cfg.get('user', 'username')
    password = token = None
    try:
        password = cfg.get('user', 'password')
    except configparser.NoOptionError:
        pass
    try:
        token = cfg.get('user', 'token')
    except configparser.NoOptionError:
        pass
    if password is None and token is None:
        raise ConfigError('''\
Your .kattisrc file appears corrupted. It must provide a token (or a
KATTIS password).

Please download a new .kattisrc file''')

    if cfg.has_option('kattis', 'loginurl'):
        loginurl = cfg.get('kattis', 'loginurl')
    else:
        loginurl = 'https://%s/%s' % (cfg.get('kattis', 'hostname'), 'login')

    return login(loginurl, username, password, token)

def login(login_url, username, password=None, token=None):
    """Log in to Kattis.

    At least one of password or token needs to be provided.

    Returns a requests.Response with cookies needed to be able to submit
    """
    login_args = {'user': username, 'script': 'true'}
    if password:
        login_args['password'] = password
    if token:
        login_args['token'] = token

    return requests.post(login_url, data=login_args, headers=_HEADERS)


def main():
    parser = argparse.ArgumentParser(prog='kattis', description='hello :)')
#     parser.add_argument('-p', '--problem',
#                         help=''''Which problem to submit to.
# Overrides default guess (first part of first filename)''')
   

    args = parser.parse_args()

    try:
        cfg = get_config()
    except ConfigError as exc:
        print(exc)
        sys.exit(1)

    try:
        login_reply = login_from_config(cfg)
    except ConfigError as exc:
        print(exc)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print('Login connection failed:', err)
        sys.exit(1)

    # Login status
    if not login_reply.status_code == 200:
        print('Login failed.')
        if login_reply.status_code == 403:
            print('Incorrect username or password/token (403)')
        elif login_reply.status_code == 404:
            print('Incorrect login URL (404)')
        else:
            print('Status code:', login_reply.status_code)
        sys.exit(1)

    # Get session page
    session = HTMLSession()
    try:
        session = HTMLSession()
        # sessionid = "bue4we"
        # sessionid = "ke376g"
        sessionid = "ksjc95"
        response = session.get("https://itu.kattis.com/sessions/%s?ajax=1" % sessionid, headers=_HEADERS)

        html:requests_html.HTML =  response.html

        # Format content to csv
        table = html.find('table[id="standings"]', first=True)
        rows = table.find('tr')
        
        data = []

        count = 0
        for r in rows:

            try:
                userObj = r.find('td>a[href]', first=True)
                userLink = userObj.attrs['href']
                user = userObj.text
            except AttributeError as e:
                userLink = None
                user = None

            try:
                scoreObj = r.find('td[class="total score"]', first=True)
                score = scoreObj.text
            except AttributeError as e:
                score = None

            data.append([count, score, user, userLink])
            count += 1

        for d in data:
            print(d)

    except requests.exceptions.RequestException as e:
        print(e)

if __name__ == '__main__':
    main()
