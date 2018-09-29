#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct
import json  # loads to decode json, dumps to encode
import dateutil.parser
import dateutil.relativedelta
from datetime import datetime
# from AtHome import get_wifi_parameters, get_default_profile
from src.GraphQLClient import GraphQLClient
from decimal import Decimal

MAX_DELAY_FROM_SAMPLE = 3600 # Seconds

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


modules_names = {
    'atmospherics': ['Air Quality', 'air quality', 'athmospherics', 'Atmospherics'],
    'thermometer': ['Temperature', 'temperature', 'Thermometer'],
    'hygrometer': ['Humidity', 'humidity', 'Hygrometer'],
    'luxmeter': ['Luminosity', 'luminosity', 'Luxmeter'],
    'soundmeter': ['noise', 'Noise', 'Sound', 'sound']
}


modules_thresholds = {
    'atmospherics': {
        'name': 'Par defaut',
        'default_min': 10,
        'current_min': 10,
        'min': 10,
        'default_max': 500,
        'current_max': 500,
        'max': 500,
    },
    'thermometer': {
        'name': 'Par defaut',
        'default_min': 17,
        'current_min': 17,
        'min': 10,
        'default_max': 30,
        'current_max': 30,
        'max': 30,
    },
    'hygrometer': {
        'name': 'Par defaut',
        'default_min': 50,
        'current_min': 50,
        'min': 35,
        'default_max': 80,
        'current_max': 80,
        'max': 80,
    },
    'luxmeter': {
        'name': 'Par defaut',
        'default_min': 800,
        'current_min': 800,
        'min': 200,
        'default_max': 3000,
        'current_max': 3000,
        'max': 3000,
    },
    'soundmeter': {
        'name': 'Par defaut',
        'default_min': 35,
        'current_min': 35,
        'min': 0,
        'default_max': 55,
        'current_max': 55,
        'max': 80,
    }
}


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
        self.password = 'AtHomeRennes8'
        self.ip = '192.168.4.1'
        self.port = 4444


def get_wifi_parameters():
    return WiFiParameters()


def get_common_name(label):
    for name, synonyms in modules_names.items():
        if label in synonyms:
            return name
    return None


def sendToAPI(module, data):
    client = GraphQLClient('http://localhost:8080/graphql')
    if data['Serial'] == 0:
        try:
            name = data['Data'][0]['Label'];
            common_name = get_common_name(name)
            module_type = common_name if not None else "Unknown"
            id = client.new_module(name, module_type)
            client.new_thresholds(id, modules_thresholds[module_type])
        except GraphQLClient.Error as e:
            print('[GraphQLClientError] %s' % e, file=sys.stderr)
            return
        print('new id:', id, file=sys.stderr)
        set_profile(module, id)
        data['Serial'] = id
        set_date_time(module)
        set_wifi(module)
        set_end_point(module)
    values = []
    for sample in data['Data']:
        if type(sample['Value']) is not dict:
            measure = Decimal(sample['Value']) * units_coefficients[sample['Prefix']]
            values.append([{
                'unit_measure': units_abbreviations[sample['Unit']],
                'measure': str(measure),
                'name': sample['Label'] if 'Label' in sample else 'Unnamed'
            }, sample['Timestamp']])
        else:
            for key, value in sample['Value'].items():
                if value is not dict:
                    measure = Decimal(value) * units_coefficients[sample['Prefix']]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[sample['Unit']])
                    name = sample['Label'] if 'Label' in sample else 'Unnamed'
                else:
                    measure = Decimal(value['Value']) * units_coefficients[value['Prefix']]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[value['Unit']])
                    name = value['Label'] if 'Label' in sample else 'Unnamed'
                values.append([{
                    'unit_measure': unit_measure,
                    'measure': str(measure),
                    'name': name
                }, sample['Timestamp']])
    for value in values:

        valueTimestamp = dateutil.parser.parse(value[1])
        timeDelta = (datetime.now() - valueTimestamp).total_seconds()
        if timeDelta > MAX_DELAY_FROM_SAMPLE:
            print("Outdated sample discarded")
            continue
        
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
    'SetEndPoint': 'SetEndPoint',
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
    mod.read(1)  # Eat the end of command
    return module_data


def set_wifi(mod):
    wifi_param = get_wifi_parameters()
    wifi = {
        'ssid': wifi_param.ssid.encode('ascii'),
        'password': wifi_param.password.encode('ascii')
    }
    mod.write(AtHomeProtocol['SetWiFi'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    # mod.write(json.dumps(wifi).replace(' ', '').encode('ascii'))
    mod.write(struct.pack('<%dsB%dsB' % (len(wifi['ssid']), len(wifi['password'])), wifi['ssid'], 0, wifi['password'],
                          0))
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_end_point(mod):
    wifi_param = get_wifi_parameters()
    endpoint = {
        'ip': [int(part) for part in wifi_param.ip.split('.')],
        'port': wifi_param.port
    }
    mod.write(AtHomeProtocol['SetEndPoint'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    # mod.write(json.dumps(endpoint).replace(' ', '').encode('ascii'))
    mod.write(struct.pack('<BBBBBH', 4, int(endpoint['ip'][0]), int(endpoint['ip'][1]), int(endpoint['ip'][2]), int(endpoint['ip'][3]),
                          endpoint['port']))
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
