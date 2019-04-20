#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# Copyright 2018 (c) huxiba@gmail.com

import sys
import getopt
import subprocess
import os.path
import re

# Nagios return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class Config(object):
    pass


def _get_os_file_quota():
    """
    get the max datafile size on OS, default is 32GB
    :return: the size in GB
    """
    quota = 32
    if os.uname().sysname.lower() == "linux":
        quota = 32
    return quota


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


def _check_rac_crs(cfg, warning=None, critical=None):
    """
    check RAC CRS daemon status using the following command
        crsctl check crs
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    bin_name = "crsctl"
    _check_attrs(cfg, ["oh", ])

    bin_name = os.path.join(cfg.oh, "bin", bin_name)
    try:
        args = bin_name + " check crs"
        cp = subprocess.run(args, shell=True, check=True, stdout=subprocess.PIPE)
        if cp.stdout is None:
            print("None result from crsctl")
            return UNKNOWN
        out = str(cp.stdout, "utf-8")
        for l in out.split(os.linesep):
            if l.lstrip().rstrip() == "":
                continue
            if not l.lstrip().rstrip().endswith("is online"):
                print(l)
                return CRITICAL
        print(out)
        return OK
    except subprocess.CalledProcessError as err:
        print(err.output)
        return UNKNOWN


def _check_rac_srv(cfg, warning=None, critical=None):
    """
    check RAC status using the following command
        srvctl status database -d $ORACLE_SID
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    regex = re.compile("Instance .* is running on node .*")
    bin_name = "srvctl"
    _check_attrs(cfg, ["sid", "oh"])
    bin_name = os.path.join(cfg.oh, "bin", bin_name)
    try:
        args = bin_name + " status database -d {sid}".format(sid=cfg.sid)
        cp = subprocess.run(args, shell=True, check=True, stdout=subprocess.PIPE)
        if cp.stdout is None:
            print("None result from crsctl")
            return UNKNOWN
        out = str(cp.stdout, "utf-8")
        running, not_running = 0, 0
        for l in out.split(os.linesep):
            if l.lstrip().rstrip() == "":
                continue
            if regex.search(l.lstrip().rstrip()):
                running += 1
            else:
                not_running += 1

        if not_running >= running:
            print("you got {0} nodes was not running".format(not_running))
            return CRITICAL
        if not_running > 0:
            print("you got {0} nodes was not running".format(not_running))
            return WARNING

        print("all {0} nodes is running".format(running))
        return OK
    except subprocess.CalledProcessError as err:
        print(err.output)
        return UNKNOWN


def _check_rac_asm(cfg, warning=None, critical=None):
    """
    check RAC ASM disk group free space using the following command
        asmcmd lsdg
    :param cfg:
    :param warning: free percent of disk group, default is 0.3
    :param critical: free percent of disk group, default is 0.1
    :return:
    """
    warning_quota = 0.3 if warning is None else warning
    critical_quota = 0.1 if critical is None else critical
    bin_name = "asmcmd"
    _check_attrs(cfg, ["sid", "user", "oh"])
    bin_name = os.path.join(cfg.oh, "bin", bin_name)
    try:
        os.environ["ORACLE_SID"] = cfg.sid
        args ="sudo -u {user} {bin} lsdg".format(user=cfg.user,bin=bin_name)
        cp = subprocess.run(args, shell=True, check=True, stdout=subprocess.PIPE)
        if cp.stdout is None:
            print("None result from asmcmd lsdg")
            return UNKNOWN
        out = str(cp.stdout, "utf-8")
        name_index, total_index, free_index = 12, 6, 7
        data = []
        for l, d in enumerate(out.split(os.linesep)):
            cols = d.lstrip().rstrip().split()
            if len(cols) == 0:
                continue
            if l == 0:
                name_index = cols.index("Name")
                total_index = cols.index("Total_MB")
                free_index = cols.index("Free_MB")
            else:
                data.append({"name": cols[name_index], "total": int(cols[total_index]), "free": int(cols[free_index])})
        for d in data:
            free_percent = d["free"] / d["total"]
            if free_percent <= critical_quota:
                print("only {0} MB free in asm disk {1}".format(d["free"], d["name"]))
                return CRITICAL
            if free_percent <= warning_quota:
                print("only {0} MB free in asm disk {1}".format(d["free"], d["name"]))
                return WARNING
        print("all asm disk free space is fine")
        return OK
    except subprocess.CalledProcessError as err:
        print(err.output)
        return UNKNOWN


def _check_rac_listener(cfg, warning=None, critical=None):
    """
    check RAC listener status
    :param cfg:
    :param warning:
    :param critical:
    :return:
    """
    bin_name = "lsnrctl"
    _check_attrs(cfg, ["sid", "oh"])
    bin_name = os.path.join(cfg.oh, "bin", bin_name)
    regex = re.compile(r'Instance "{0}\d*", status READY, has 1 handler\(s\) for this service...'.format(cfg.sid))

    try:
        os.environ["ORACLE_HOME"] = cfg.oh
        args = bin_name + " status"
        cp = subprocess.run(args, shell=True, check=True, stdout=subprocess.PIPE)
        if cp.stdout is None:
            print("None result from lsnrctl status")
            return UNKNOWN
        out = str(cp.stdout, "utf-8")
        ready = False
        msg = "Service {0} has 0 listener status is READY".format(cfg.sid)
        for l in out.split(os.linesep):
            if regex.search(l.lstrip().rstrip()):
                ready = True
                msg = l
                break

        print(msg)
        return OK if ready else CRITICAL
    except subprocess.CalledProcessError as err:
        print(err.output)
        return UNKNOWN


def _get_seconds(time_str):
    if time_str is None:
        return None
    m = re.match(r"^\+(\d{2})\s(\d{2}):(\d{2}):(\d{2})\.?(\d{0,3})$", time_str)
    if m is None:
        return None
    return int(m.group(1)) * 24 * 60 * 60 + int(m.group(2)) * 60 * 60 + int(m.group(3)) * 60 + int(m.group(4))


def _get_seconds_str(time_str):
    if time_str is None:
        return None
    m = re.match(r"^\+(\d{2})\s(\d{2}):(\d{2}):(\d{2})\.?(\d{0,3})$", time_str)
    if m is None:
        return None
    r = str(int(m.group(4))) + "秒"
    if int(m.group(3)) > 0:
        r = str(int(m.group(3))) + "分" + r
    if int(m.group(2)) > 0:
        r = str(int(m.group(2))) + "小时" + r
    if int(m.group(1)) > 0:
        r = str(int(m.group(1))) + "天" + r
    return r


def main():
    """
    check_ora_rac.py -m model ......
    -m, --model
        check model
            rac_crs               check rac crs daemon using crsctl
            rac_srv               check rac using srvctl
            rac_asm               check rac asm disk group using asmcmd
            rac_listener          check rac listener using lsnrctl
    --oh
        ORACLE_HOME, when check rac_xxxx, you should using GRID home (/u01/app/11.2.0/grid)
                     when check db_xxxx, you should using ORACLE home (/u01/app/oracle/product/11.2.0/db_1)
    --sid
        ORACLE_SID, when check rac_asm, you should using +ASM1/+ASM2 ....
                    when check rac_***, you should using dbname1/dbname2 ....
                    when check db_****, you should using ORACLE_UNQNAME (dbname)
    -w
        warning
    -c
        critical
    :return:
    """
    parameters = ("sid", "user", "oh", )
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:w:c:", [x + "=" for x in parameters])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(UNKNOWN)

    check = "rac_crs"
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

    current_module = sys.modules[__name__]
    method = getattr(current_module, "_check_" + check)
    r = method(cfg, warning, critical)
    if r > OK:
        sys.exit(r)


if __name__ == "__main__":
    main()
