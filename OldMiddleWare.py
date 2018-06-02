#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import glob
import sys
import struct
import json  # loads to decode json, dumps to encode
import dateutil.parser
from datetime import datetime
# from AtHome import get_wifi_parameters, get_default_profile
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from src.GraphQLClient import GraphQLClient
from decimal import Decimal


units = [
    'Unknown',
    'metre',
    'kilogram',
    'second',
    'kelvin',
    'mole',
    'candela',
    'radian',
    'steradian',
    'hertz',
    'newton',
    'pascal',
    'joule',
    'watt',
    'coulomb',
    'volt',
    'farad',
    'ohm',
    'siemens',
    'weber',
    'tesla',
    'henry',
    'degree celsius',
    'lumen',
    'lux',
    'becquerel',
    'gray',
    'grevert',
    'katal',
    'part per million',
    'relative humidity',
    'aggregate'
]

units_abbreviations = [
    'Unknown',
    'm',
    'kg',
    's',
    'A',
    'K',
    'mol',
    'cd',
    'rad',
    'strad',
    'Hz',
    'N',
    'Pa',
    'J',
    'W',
    'C',
    'V',
    'F',
    'Ohm',
    'S',
    'Weber',
    'Tesla',
    'H',
    '°C',
    'Lumen',
    'lux',
    'Bcq',
    'Gray',
    'Sievert',
    'Katal',
    'PPM',
    '%RH'
]

units_coefficients = [
    Decimal(1.),
    Decimal(10.),
    Decimal(100.),
    Decimal(1000.),
    Decimal(1000000.),
    Decimal(1000000000.),
    Decimal(1000000000000.),
    Decimal(1000000000000000.),
    Decimal(1000000000000000000.),
    Decimal(1000000000000000000000.),
    Decimal(1000000000000000000000000.),
    Decimal(0.1),
    Decimal(0.01),
    Decimal(0.001),
    Decimal(0.000001),
    Decimal(0.000000001),
    Decimal(0.000000000001),
    Decimal(0.000000000000001),
    Decimal(0.000000000000000001),
    Decimal(0.000000000000000000001),
    Decimal(0.000000000000000000000001)
]


class WiFiParameters:
    def __init__(self):
        self.ssid = 'AtHome'
        self.password = '12345678'
        self.ip = '10.0.0.1'
        self.port = 4242


def get_wifi_parameters():
    return WiFiParameters()


def sendToAPI(module, data):
    client = GraphQLClient('http://localhost:8080/graphql')
    if data['Serial'] == 0:
        try:
            id = client.new_module()
        except GraphQLClient.Error as e:
            print('[GraphQLClientError] %s' % e, file=sys.stderr)
            return
        print('new id:', id, file=sys.stderr)
        set_profile(module, id)
        data['Serial'] = id
        set_date_time(module)
    values = []
    for sample in data['Data']:
        if type(sample['Value']) is not dict:
            measure = Decimal(sample['Value']) * units_coefficients[sample['Prefix']]
            values.append([{
                'unit_measure': units_abbreviations[sample['Unit']],
                'measure': str(measure),
                'name': sample['Label'] if 'label' in sample else 'Unnamed'
            }, sample['Timestamp']])
        else:
            for key, value in sample['Value'].items():
                if value is not dict:
                    measure = Decimal(value) * units_coefficients[sample['Prefix']]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[sample['Unit']])
                    name = sample['Label'] if 'label' in sample else 'Unnamed'
                else:
                    measure = Decimal(value['Value']) * units_coefficients[value['Prefix']]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[value['Unit']])
                    name = value['Label'] if 'label' in sample else 'Unnamed'
                values.append([{
                    'unit_measure': unit_measure,
                    'measure': str(measure),
                    'name': name
                }, sample['Timestamp']])
    for value in values:
        try:
            client.send_sample(data['Serial'], json.dumps(value[0]), dateutil.parser.parse(value[1]).strftime(
                '%Y-%m-%d %H:%M:%S.%f'))
        except GraphQLClient.Error as e:
            print('[GraphQLClientError] %s' % e, file=sys.stderr)


AtHomeProtocol = {
    'spacer': '\t',
    'end_of_command': '\x03',
    'end_of_communication': '\x04',
    'end_of_line': '\r\n',
    'part_separator': '=' * 80,
    'UploadData': 'UploadData',
    'SetWiFi': 'SetWiFi',
    'SetEndPoint': 'SetEndPont',
    'SetProfile': 'SetProfile',
    'SetDateTime': 'SetDateTime',
    'SSID': 'ssid',
    'Password': 'password',
    'ip': 'ip',
    'port': 'port'
}


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
    module_data = json.loads(content)
    print('UploadData:', module_data, file=sys.stderr)
    sendToAPI(mod, module_data)
    return module_data


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


def set_profile(mod, id=0):
    mod.write(AtHomeProtocol['SetProfile'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(struct.pack('<I', id))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_date_time(mod):
    mod.write(AtHomeProtocol['SetDateTime'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    now = datetime.now()
    mod.write(struct.pack('<BBBBBH', now.second, now.minute, now.hour, now.day, now.month, now.year))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


AtHomeCommands = {
    'UploadData': upload_data,
    'SetWiFi': set_wifi,
    'SetEndPoint': set_end_point,
    'SetProfile': set_profile,
    'SetDateTime': set_date_time,
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
