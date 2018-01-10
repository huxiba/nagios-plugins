#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getopt
import sys
import requests
from requests.auth import HTTPBasicAuth

# Nagios return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class Config(object):
    pass


def _check_attrs(cfg, attrs):
    """
    check cfg object has attrs ?
    :param cfg:
    :param attrs:
    :return:
    """
    for a in attrs:
        if (not hasattr(cfg, a)) or getattr(cfg, a) is None:
            print("{0} parameter is not set".format(a))
            sys.exit(UNKNOWN)


def _get_console_response(url, user, password):
    """
    return weblogic console response
    :param url:
    :param user:
    :param password:
    :return:
    """
    ba = HTTPBasicAuth(username=user, password=password)
    try:
        with requests.get(url, headers={"Accept": "application/json"}, auth=ba) as r:
            if r.status_code == 200:
                return r.json()
            else:
                print()
    except requests.RequestException as err:
        print("error ocour when make requests to {0}".format(err.request.url))
        sys.exit(UNKNOWN)


def _check_server(cfg, warning, critical):
    """
    check servers(admin server and managed servers) status
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    warning_quota = 1 if warning is None else warning
    critical_quota = 3 if critical is None else critical
    data = _get_console_response(cfg.url, cfg.user, cfg.password)
    not_ok = []
    for s in data["body"]["items"]:
        if s["state"] != "RUNNING" or s["health"] != "HEALTH_OK":
            not_ok.append(s["name"])
    if len(not_ok) == 0:
        print("all servers health are OK")
        return OK
    else:
        print("server[{0}] is not running or health".format(not_ok))
        if len(not_ok) >= critical_quota:
            return CRITICAL
        elif len(not_ok) >= warning_quota:
            return WARNING
        else:
            return UNKNOWN


def _check_ear(cfg, warning, critical):
    """
    check application status
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    data = _get_console_response(cfg.url, cfg.user, cfg.password)
    not_ok = []
    if data["body"]["item"]["state"] == "STATE_ACTIVE" and data["body"]["item"]["health"] == "HEALTH_OK":
        print("application health is ok")
        return OK
    else:
        print("application health is NOT ok on server cluster")
        return CRITICAL


def _check_datasource(cfg, warning, critical):
    """
    check databsource status
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    warning_quota = 1 if warning is None else warning
    critical_quota = 3 if critical is None else critical
    data = _get_console_response(cfg.url, cfg.user, cfg.password)
    not_ok = []
    for s in data["body"]["item"]["instances"]:
        if s["state"] != "Running" and (not s["enabled"]):
            not_ok.append(s["server"])
    if len(not_ok) == 0:
        print("all database datasource is ok")
        return OK
    else:
        print("{0} servers database datasouce is not ok".format(len(not_ok)))
        if len(not_ok) >= critical_quota:
            return CRITICAL
        elif len(not_ok) >= warning_quota:
            return WARNING
        else:
            return UNKNOWN


def main():
    """
    check_oracle.py -m model --sid=nnnnn --host=nnnnn ......
    -m, --model
        check model
            server                check servers (admin and managed servers) status
                http://host:port/management/tenant-monitoring/servers
            ear                   check application status
                http://host:port/management/tenant-monitoring/applications/application_name
            datasource            check datasource status
                http://host:port/management/tenant-monitoring/datasources/datasource_name
    --host
        weblogic admin console ip
    --port
        weblogic admin console port
    --user
        weblogic admin console user
    --password
        weblogic admin console password
    -w
        warning
    -c
        critical
    :return:
    """
    parameters = ("url", "user", "password", "host", "port")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:w:c:", [x + "=" for x in parameters])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(UNKNOWN)

    check = "server"
    cfg = Config()
    warning = None
    critical = None
    for o, a in opts:
        if o == "-m":
            check = a.lower()
        if o == "-w":
            warning = float(a)
        if o == "-c":
            critical = float(a)
        if o.startswith("--"):
            setattr(cfg, o[2:], a)
    _check_attrs(cfg, parameters)
    cfg.url = "http://{host}:{port}/{url}".format(host=cfg.host, port=cfg.port, url=cfg.url)
    current_module = sys.modules[__name__]
    method = getattr(current_module, "_check_" + check)
    r = method(cfg, warning, critical)
    if r > OK:
        sys.exit(r)


if __name__ == "__main__":
    main()
