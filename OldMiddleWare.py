#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import glob
import sys
import struct
import json  # loads to decode json, dumps to encode
import threading
# from AtHome import get_wifi_parameters, get_default_profile
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


class WiFiParameters:
    def __init__(self):
        self.ssid = 'AtHome'
        self.password = '12345678'
        self.ip = '10.0.0.1'
        self.port = 4242


class ModuleProfile:
    def __init__(self):
        self.vendor = b'AtHome\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
        self.serial = b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
        self.type = 0


def get_wifi_parameters():
    return WiFiParameters()


def get_default_profile():
    return ModuleProfile()


AtHomeProtocol = {
    'spacer': '\t',
    'end_of_command': '\x03',
    'end_of_communication': '\x04',
    'end_of_line': '\r\n',
    'part_separator': '=' * 80,
    'Enumerate': 'Enumerate',
    'UploadData': 'UploadData',
    'SyncTime': 'SyncTime',
    'SetWiFi': 'SetWiFi',
    'SetEndPoint': 'SetEndPont',
    'SetProfile': 'SetProfile',
    'SSID': 'ssid',
    'Password': 'password',
    'ip': 'ip',
    'port': 'port'
}


def enumerate_module(mod):
    first_line = ''
    while first_line.endswith(AtHomeProtocol['end_of_line']) is False:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(30000)
            continue
        first_line += data.decode('ascii')
    content = ''
    while content.endswith(AtHomeProtocol['end_of_line']) is False:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(30000)
            continue
        content += data.decode('ascii')
    return json.loads(content)


def upload_data(mod):
    first_line = ''
    while first_line.endswith(AtHomeProtocol['end_of_line']) is False:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(30000)
            continue
        first_line += data.decode('ascii')
    content = ''
    while content.endswith(AtHomeProtocol['end_of_line']) is False:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(30000)
            continue
        content += data.decode('ascii')
    return json.loads(content)


def sync_time(mod):
    mod.write(AtHomeProtocol['SyncTime'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(struct.pack('<Q', int(time.mktime(time.localtime()))))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_wifi(mod):
    wifi_param = get_wifi_parameters()
    wifi = {
        'ssid': wifi_param.ssid,
        'password': wifi_param.password
    }
    mod.write(AtHomeProtocol['SetWiFi'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(json.dumps(wifi).replace(' ', '').encode('ascii'))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_end_point(mod):
    wifi_param = get_wifi_parameters()
    endpoint = {
        'ip': wifi_param.ip,
        'port': wifi_param.port
    }
    mod.write(AtHomeProtocol['SetEndPoint'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(json.dumps(endpoint).replace(' ', '').encode('ascii'))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_profile(mod):
    profile = get_default_profile()
    mod.write(AtHomeProtocol['SetProfile'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(struct.pack('<33s33sB', profile.vendor, profile.serial, profile.type))
    mod.write(AtHomeProtocol['end_of_communication'].encode('ascii'))
    return None


AtHomeCommands = {
    'Enumerate': enumerate_module,
    'UploadData': upload_data,
    'SyncTime': sync_time,
    'SetWiFi': set_wifi,
    'SetEndPoint': set_end_point,
    'SetProfile': set_profile
}


def open_serial_port(name):
    try:
        serial_port = QSerialPort()
        serial_port.setPortName(name)
        serial_port.setBaudRate(QSerialPort.Baud115200, QSerialPort.AllDirections)
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
    """ LIst les ports séries disponible et leurs noms
    :raise EnvironmentError:
        Plateforme inconnue
    :return:
        LAl ist des ports serial dispo sur le système
    """
    if sys.platform.startswith('linux'):
        ports = glob.glob('/dev/pts/*')
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
            command = command[: - len(AtHomeProtocol['end_of_line'])]
            if command in AtHomeCommands:
                AtHomeCommands[command](serial_port)
            else:
                raise NameError("[Unknown command] %s" % command)


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
