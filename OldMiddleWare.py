#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import glob
# from AtHome import get_wifi_parameters, get_default_profile
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from os import fork
from middleware_common import *


def open_serial_port(name):
    try:
        serial_port = QSerialPort()
        serial_port.setPortName(name)
        serial_port.setBaudRate(QSerialPort.Baud9600, QSerialPort.AllDirections)
        serial_port.setParity(QSerialPort.NoParity)
        serial_port.setStopBits(QSerialPort.OneStop)
        serial_port.setDataBits(QSerialPort.Data8)
        serial_port.setFlowControl(QSerialPort.NoFlowControl)
        serial_port.open(QSerialPort.ReadWrite)
        return serial_port
    except Exception as e:
        print("open_serial_port", e)
        return None


def get_serial_ports():
    """ List les ports séries disponible et leurs noms
    :raise EnvironmentError:
        Plateforme inconnue
    :return:
        La list des ports serial dispo sur le système
    """
    # if sys.platform.startswith('linux'):
    #     serial_ports = glob.glob('/dev/athome*')
    # else:
    info_list = QSerialPortInfo()
    serial_list = info_list.availablePorts()
    serial_ports = [port.portName() for port in serial_list]
    return serial_ports


def parse_command(serial_port):
    command = ""
    while True:
        data = serial_port.read(1)
        if data == b'':
            serial_port.waitForReadyRead(1000)
            continue
        else:
            data = data.decode('ascii')
        if data == AtHomeProtocol['end_of_communication']:
            raise NameError("Communication Ended")
        if data != AtHomeProtocol['end_of_command']:
            command += data
        else:
            command = ""
            continue
        if command.endswith(AtHomeProtocol['end_of_line']):
            command = command[0:-len(AtHomeProtocol['end_of_line'])].upper()
            if command in AtHomeCommands:
                print("[Detected command]", command, file=sys.stderr)
                AtHomeCommands[command](serial_port)
            else:
                print("[Unknown command]", command, file=sys.stderr)
            command = ""


def read_data_from_serial(port=None):
    if port is None:
        return
    while True:
        try:
            parse_command(port)
        except Exception as e:
            print("read_data_from_serial", e, file=sys.stderr)
            if port.isOpen() is False:
                return


def detect_new_modules(current_modules):
    # modules = glob.glob('/dev/athome*')
    modules= get_serial_ports()
    new_modules = []
    for module in modules:
        if module not in current_modules:
            new_modules.append(module)
    return new_modules


def start_module_daemon(module):
    if fork() == 0:
        read_data_from_serial(open_serial_port(module))
    # sys.exit(0)


if __name__ == "__main__":
    a = QCoreApplication(sys.argv)
    serial_res = []
    if len(sys.argv) > 1:
        serial_res += sys.argv[1:]
    serial_res += get_serial_ports()
    for port in serial_res:
        start_module_daemon(port)
    sys.exit(0)
    while True:
        time.sleep(1)
        new_modules = detect_new_modules(serial_res)
        for module in new_modules:
            start_module_daemon(module)
            serial_res.append(module)
