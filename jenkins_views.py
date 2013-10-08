#!/usr/bin/env python

from __future__ import print_function

import argparse
import base64
import json
import urlparse
import sys


def http_fetch(url, username=None, password=None):
    import urllib2
    request = urllib2.Request(url, None)
    if username is not None:
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
    try:
        return urllib2.urlopen(request)
    except:
        print('While fetching <{0}>:'.format(url), file=sys.stderr)
        if username is not None:
            print('Using username <{0}>'.format(username), file=sys.stderr)
        raise


def api_fetch(url, username=None, password=None):
    url = urlparse.urljoin(url, 'api/json')
    return json.load(http_fetch(url, username, password))


def main():
    parser = argparse.ArgumentParser(description='Print the names of Jenkins views')
    parser.add_argument('server', help='URL of Jenkins server')
    parser.add_argument('--username', '-u', help='Jenkins username')
    parser.add_argument('--password', '-p', help='Jenkins password')

    args = parser.parse_args()

    views_url = urlparse.urljoin(args.server, "/api/json/views")

    for view in api_fetch(views_url, args.username, args.password)['views']:
        if view['name'] not in ['All', '_Active', '_Disabled']:
            print(view['name'])

if __name__ == '__main__':
    main()
