#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import json
import sys
from datetime import datetime

url='https://oapi.dingtalk.com/robot/send?access_token=tokenid'


def sendmessage(message):
    msg={"msgtype": "text", "text":{"content": message}}
    params=json.dumps(msg).encode('utf-8')
    req=urllib.request.Request(url, data=params, headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        pass


args = sys.argv
msg = ""

for line in sys.stdin:
    msg += line

msg += "\n\n Reported at "+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
sendmessage(msg)