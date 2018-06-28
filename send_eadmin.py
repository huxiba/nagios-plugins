#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import sys
from datetime import datetime

url = 'http://zzzzzz/api/upload.php'


def sendmessage(message):
    print(message)
    params = urllib.parse.urlencode(message)
    params = params.encode("ascii")
    req = urllib.request.Request(url, data=params, headers={'content-type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req) as response:
        #print(response.read().decode("unicode_escape"))
        #print(response.getcode())
        pass


args = sys.argv
msg = {"act": "serverwarning",
       "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), }

for line in sys.stdin:
    if line is not None and line.strip() != "":
        k, v = line.split(":")
        msg[k] = v.strip()

sendmessage(msg)