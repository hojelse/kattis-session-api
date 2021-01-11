#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import re
import sys
from requests_html import HTMLSession
import json

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

def json_formatted_generator(json_text):
    obj = json.loads(json_text)

    useridToName = {}
    problemNameToId = {}
    problemIdToName = []

    it = 0
    for s in obj['sessions']:
        name = s['problems']['A']['problem_name']
        problemNameToId[name] = it
        problemIdToName.append(name)
        it += 1

    personToSolved = {}

    for s in obj['students']:
        username = s['username']
        personToSolved[username] = []
        useridToName[username] = s['name']

    for t in obj['teachers']:
        username = t['username']
        personToSolved[username] = []
        useridToName[username] = t['name']

    for s in obj['sessions']:
        for r in s['results']:
            for p in r['problems']:
                for m in r['members']:
                    problemid = problemNameToId[p['problem_name']]
                    personToSolved[m].append(problemid)
    
    for p in personToSolved:
        output = useridToName[p] + "(" + p + ") : "
        try:
            for i in personToSolved[p]:
                output += problemIdToName[i] + ", "
        except KeyError as e:
            output += None
        yield output


def main():
    parser = argparse.ArgumentParser(prog='get-session.py', description='Get the data from a kattis session i.e. <sub_domain>.kattis.com/sessions/<session_id>')
    parser.add_argument('-c', '--courseid',
        help='''Which course to get data from. Overrides default "KSALDAS/2021-Spring"''')
    parser.add_argument('-f', '--file',
        help='''Used for testing. Parses and prints a local JSON file.''')
    parser.add_argument('-o', '--output',
        help='''Used for testing. Gets and prints course JSON file.''')

    args = parser.parse_args()

    courseid = 'KSALDAS/2021-Spring'
    if(args.courseid is not None):
        courseid = args.courseid

    if(args.file is not None):
        f = open(args.file, "r")
        for line in json_formatted_generator(f.read()):
            print(line)
        sys.exit(1)

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
    try:

        response = requests.get("https://itu.kattis.com/courses/%s/export?type=results&submissions=lastaccepted" % courseid, cookies=login_reply.cookies, headers=_HEADERS)

        json_text = json.dumps(json.loads(response.text))

        if(args.output is not None):
            sys.stdout = open('course.json', 'w')
            print(json_text)
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print('Json download connection failed', e)
        sys.exit(1)

    for line in json_formatted_generator(json_text):
        print(line)

if __name__ == '__main__':
    main()
