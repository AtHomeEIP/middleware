#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import glob
# from AtHome import get_wifi_parameters, get_default_profile
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
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
        print(e)
        return None


def get_serial_ports():
    """ List les ports séries disponible et leurs noms
    :raise EnvironmentError:
        Plateforme inconnue
    :return:
        La list des ports serial dispo sur le système
    """
    if sys.platform.startswith('linux'):
        ports = glob.glob('/dev/tyyACM*')
    else:
        ports = []
    info_list = QSerialPortInfo()
    serial_list = info_list.availablePorts()
    serial_ports = [open_serial_port(port) for port in ports]
    serial_ports += [open_serial_port(port) for port in serial_list]
    return serial_ports


def parse_command(serial_port):
    command = ""
    while True:
        data = serial_port.read(1)
        if data == b'':
            serial_port.waitForReadyRead(30000)
            continue
        else:
            data = data.decode('ascii')
        if data == AtHomeProtocol['end_of_communication']:
            raise NameError("Communication Ended")
        command += data
        if command.endswith(AtHomeProtocol['end_of_line']):
            command = command[0:-2]
            if command in AtHomeCommands:
                AtHomeCommands[command](serial_port)
            else:
                raise NameError("[Unknown command] %s" % command)
            command = ""


def read_data_from_serial(port=None):
    if port is None:
        return
    while True:
        try:
            port.waitForReadyRead(30000)
            parse_command(port)
        except Exception as e:
            print(e, file=sys.stderr)


if __name__ == "__main__":
    a = QCoreApplication(sys.argv)
    if len(sys.argv) > 1:
        serial_res = [open_serial_port(port) for port in sys.argv[1:]]
    else:
        serial_res = get_serial_ports()
    for port in serial_res:
        # thread = threading.Thread(target=read_data_from_serial, kwargs={'port': port})
        # thread.start()
        read_data_from_serial(port)
    while True:
        time.sleep(1)
