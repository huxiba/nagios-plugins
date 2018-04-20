#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import fileinput

command = ""
'''
格式
手机号码,手机号码|短信内容

lsusb -v
minicom --device /dev/ttyUSB0
'''

with fileinput.input("-") as f:
    for l in f:
        command += l
command = command[:-1]
phones = command.split("|")[0].split(",")
msg = command.split("|")[1]

pdus = []
for i, p in enumerate([x+"F" for x in phones]):
    pdus.append("0011000B81")
    '''
    00--短消息中心信息的长度，这里的0意味着，采用modem中已存的短消息中心的信息。
    11--说明信息体格式的字段，普通短信和wap push在这个字段上会有区别的。（普通短信就用11）
    00--一般取00，采用默认的发送号码。
    0B--接收手机号码长度的十六进制表示。中国大陆应该都是0B（11=0BH）。
    81--本部分表明了接受手机号码的类型。这里采用81。
    '''
    for n in range(0, len(p), 2):
        '''
        接收的手机号码是13812345678，手机号是11位奇数，末尾加F
        将原号码变为13812345678F，然后我们把第一位和第二位交换，第三位和第四位交换
        '''
        pdus[i] += p[n+1:n+2]
        pdus[i] += p[n:n+1]
    pdus[i] += "0008A7"
    '''
    00--协议标识(TP-PID) 是普通GSM类型，点到点方式。
    08--用户信息编码方式UCS2。
    在PDU Mode中，可以采用三种编码方式来对发送的内容进行编码，它们是7-bit、8-bit和UCS2（16-bit）编码。
    7-bit编码用于发送普通的ASCII字符，它将一串7-bit的字符(最高位为0)编码成8-bit的数据；
    8-bit编码通常用于发送数据消息，比如图片和铃声等；
    UCS2编码用于发送Unicode字符。
    PDU串的用户信息(TP-UD)段最大容量是140字节，所以在这三种编码方式下，可以发送的短消息的最大字符数分别是160、140和70。这里，将一个英文字母、一个汉字和一个数据字节都视为一个字符。
    A7--信息有效期
    '''
    m = msg.encode('utf-16be').hex().upper()

    '''
    msg前面加上长度标识
    '''
    pdus[i] += "{:02X}{:s}".format(int(len(m)/2), m)

with serial.Serial("/dev/ttyUSB0", timeout=5, write_timeout=5, exclusive=True) as s:
    s.write("AT+CSCS=UCS2\r".encode())
    s.flush()
    r = ""
    while r.find("OK\r\n") < 0 and r.find("ERROR\r\n") < 0:
        t = s.read(65535)
        r += t.decode("UTF-8")
        time.sleep(0.1)

    for pdu in pdus:
        s.write("AT+CMGS={:d}\r".format(int(len(pdu)/2-1)).encode())
        r = ""
        while r.find("> ") < 0:
            t = s.read(12)
            r += t.decode("UTF-8")
            time.sleep(0.1)
        s.write((pdu+chr(26)).encode())

        r = ""
        while r.find("OK\r\n") < 0 and r.find("ERROR\r\n") < 0:
            t = s.read(65535)
            r += t.decode("UTF-8")
            time.sleep(0.1)
