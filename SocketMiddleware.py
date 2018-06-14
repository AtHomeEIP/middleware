#!/usr/bin/env python3
# -*- coding: utf-*- -*-

from middleware_common import *
from os import fork
from time import sleep
import socket
import sys


def listen_on_socket(socket, *args):
    if socket is None:
        return
    command = ""
    file = socket.makefile('rwb')
    while True:
        try:
            data = file.read(1)
            if data == b'':
                sleep(0.001)
                continue
            else:
                data = data.decode('ascii')
            if data == AtHomeProtocol['end_of_communication']:
                print('Communication ended', file=sys.stderr)
                return
            command += data
            if command.endswith(AtHomeProtocol['end_of_line']):
                command = command[0:-2]
                if command in AtHomeCommands:
                    AtHomeCommands[command](file)
                else:
                    command = ""
                    raise NameError('[Unknown Command] %s' % command)
                command = ""
        except EOFError:
            file.close()
            socket.close()
            sys.exit(0)
        except Exception as e:
            print('[Exception] %s' % e, file=sys.stderr)


if __name__ == "__main__":
    socket = socket.socket()
    socket.bind(('0.0.0.0', 4444))
    socket.listen(5)
    while True:
        conn, address = socket.accept()
        if conn is not None:
            print('Accepted connection', file=sys.stderr)
            if fork() == 0:
                listen_on_socket(conn, address)
            else:
                conn.close()
        sleep(0.001)
