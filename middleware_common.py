#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct
import json  # loads to decode json, dumps to encode
import dateutil.parser
import dateutil.relativedelta
import paho.mqtt.publish as publish
import netifaces
import os
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


def athome_update_crc(crc, a):
    crc = crc ^ a
    for i in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xA001
        else:
            crc = (crc >> 1)
    return crc


def athome_crc(data):
    if type(data) is not bytes:
        raise NameError("Not bytes serialized data")
    crc = 0xFF
    for byte in data:
        crc = athome_update_crc(crc, byte)
    return crc


class WiFiParameters:
    def __init__(self):
        self.ssid = os.environ.get('ATHOME_WIFI_SSID', 'ATHOME')
        self.password = os.environ.get('ATHOME_WIFI_PASSWORD', 'ATHOME_DEFAULT')
        self.ip = os.environ.get('ATHOME_IP', netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr'])
        self.port = int(os.environ.get('ATHOME_PORT', 4444))


def get_wifi_parameters():
    return WiFiParameters()


def get_common_name(label):
    for name, synonyms in modules_names.items():
        if label in synonyms:
            return name
    return None

from src.CloudClient import CloudClient

insertingModuleInDb = False

def sendToAPI(module, data):
    client = GraphQLClient('http://localhost:8080/graphql')
    cloudClient = CloudClient(api_url='https://woodbox.io/graphql')

    if data['Serial'] == 0 and insertingModuleInDb is False:
        global insertingModuleInDb = True
        try:
            name = data['Data'][0]['Label']
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
    else if data['Serial'] != 0:
        global insertingModuleInDb = False
    values = []
    for sample in data['Data']:
        if type(sample['Value']) is not dict:
            measure = Decimal(sample['Value']) * units_coefficients[int(sample['Prefix'].hex(), 16)]
            values.append([{
                'unit_measure': units_abbreviations[int(sample['Unit'].hex(), 16)],
                'measure': str(measure),
                'name': sample['Label'] if 'Label' in sample else 'Unnamed'
            }, sample['Timestamp']])
        else:
            for key, value in sample['Value'].items():
                if value is not dict:
                    measure = Decimal(value) * units_coefficients[int(sample['Prefix'].hex(), 16)]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[int(sample['Unit'].hex(), 16)])
                    name = sample['Label'] if 'Label' in sample else 'Unnamed'
                else:
                    measure = Decimal(value['Value']) * units_coefficients[int(value['Prefix'].hex(), 16)]
                    unit_measure = '%s(%s)' % (key, units_abbreviations[int(value['Unit'].hex(), 16)])
                    name = value['Label'] if 'Label' in sample else 'Unnamed'
                values.append([{
                    'unit_measure': unit_measure,
                    'measure': str(measure),
                    'name': name
                }, sample['Timestamp']])
    for value in values:
        # valueTimestamp = dateutil.parser.parse(value[1])
        # timeDelta = (datetime.now() - valueTimestamp).total_seconds()
        # if timeDelta > MAX_DELAY_FROM_SAMPLE:
        #     print("Outdated sample discarded")
        #     continue

        # same # nowTimeStamp = dateutil.parser.parse(value[1])
        nowTimeStamp = datetime.now()
        
        try:
            client.send_sample(data['Serial'], json.dumps(value[0]), nowTimeStamp.strftime(
                '%Y-%m-%d %H:%M:%S.%f'))
            publish.single("athome", json.dumps(value, ensure_ascii=False).encode('utf-8'), qos=2)
            # cloudClient.send_sample()
        except GraphQLClient.Error as e:
            print('[GraphQLClientError] %s' % e, file=sys.stderr)


AtHomeProtocol = {
    'spacer': '\t',
    'end_of_command': '\x03',
    'end_of_communication': '\x04',
    'end_of_line': '\n',
    'part_separator': '=' * 80,
    'UploadData': 'UPLOAD_DATA',
    'SetWiFi': 'SET_WIFI',
    'SetEndPoint': 'SET_END_POINT',
    'SetProfile': 'SET_PROFILE',
    'SetDateTime': 'SET_DATE_TIME',
    'SSID': 'ssid',
    'Password': 'password',
    'ip': 'ip',
    'port': 'port'
}


def parse_varuint(mod):
    parsing = True
    value = 0
    it = 0
    while parsing is True:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(1000)
            continue
        data = data[0]
        parsing = True if data & 0x80 else False
        data = (data & 0x7F) << (7 * it)
        value |= data
        it += 1
    return value


def parse_string(mod):
    parsing = True
    string = b''
    while parsing is True:
        data = mod.read(1)
        if data == b'':
            mod.waitForReadyRead(1000)
            continue
        elif data == b'\0':
            parsing = False
        else:
            string += data
    return string.decode('ascii')


def parse_byte(mod):
    b = mod.read(1)
    if b == b'':
        mod.waitForReadyRead(1000)
        return parse_byte(mod)
    else:
        return b


def parse_date_time(mod):
    tmp = [parse_byte(mod) for i in range(6)]
    return {
        'second': int(tmp[0].hex(), 16),
        'minute': int(tmp[1].hex(), 16),
        'hour': int(tmp[2].hex(), 16),
        'day': int(tmp[3].hex(), 16),
        'month': int(tmp[4].hex(), 16),
        'year': int(tmp[5].hex(), 16),
    }


def upload_data(mod):
    serial = parse_varuint(mod)
    year = parse_varuint(mod)
    nb_measures = parse_varuint(mod)
    data = []
    prev_data = {}
    for i in range(nb_measures):
        fields = parse_varuint(mod)
        label = prev_data['Label'] if not fields & 0x1 else parse_string(mod)
        unit = prev_data['Unit'] if not fields & 0x2 else parse_byte(mod)
        prefix = prev_data['Prefix'] if not fields & 0x4 else parse_byte(mod)
        estimate = prev_data['Estimate'] if not fields & 0x8 else parse_byte(mod)
        sample = prev_data['Value'] if not fields & 0x10 else parse_string(mod)
        timestamp = prev_data['Timestamp'] if not fields & 0x20 else parse_date_time(mod)
        timestamp['year'] += year if fields & 0x20 else 0
        decoded_sample = None
        try:
            decoded_sample = json.loads(sample) if fields & 0x10 else prev_data['Value']
        except json.JSONDecodeError:
            decoded_sample = sample
        prev_data = {
            'Value': decoded_sample,
            'Label': label,
            'Unit': unit,
            'Prefix': prefix,
            'Estimate': estimate,
            'Timestamp': timestamp
        }
        data.append(prev_data)
    parse_byte(mod)
    print(data)
    sendToAPI(mod, {
        'Serial': serial,
        'Data': data
    })
    return None


def set_wifi(mod):
    wifi_param = get_wifi_parameters()
    wifi = {
        'ssid': wifi_param.ssid.encode('ascii'),
        'password': wifi_param.password.encode('ascii')
    }
    mod.write(AtHomeProtocol['SetWiFi'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    # mod.write(json.dumps(wifi).replace(' ', '').encode('ascii'))
    ssid = wifi['ssid']
    password = wifi['password']
    crc_ssid = athome_crc(ssid)
    crc_password = athome_crc(password)
    mod.write(struct.pack('<H', crc_ssid))
    mod.write(ssid + bytes([0]))
    mod.write(struct.pack('<H', crc_password))
    mod.write(password + bytes([0]))
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
    ip = struct.pack('<BBBB', int(endpoint['ip'][0]), int(endpoint['ip'][1]), int(endpoint['ip'][2]), int(endpoint['ip'][3]))
    port = struct.pack('<H', endpoint['port'])
    crc_ip = athome_crc(ip)
    crc_port = athome_crc(port)
    mod.write(struct.pack('<B', 4))
    mod.write(struct.pack('<H', crc_ip))
    mod.write(ip)
    mod.write(struct.pack('<H', crc_port))
    mod.write(port)
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_profile(mod, new_id=0, password='default', encryption_key=b'00000000000000000000000000000000', encryption_iv=b'000000000000'):
    mod.write(AtHomeProtocol['SetProfile'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    b_id = struct.pack('<I', new_id)
    crc_id = athome_crc(b_id)
    b_password = password.encode('ascii')
    crc_password = athome_crc(b_password)
    mod.write(struct.pack('<H', crc_id))
    mod.write(b_id)
    mod.write(struct.pack('<H', crc_password))
    mod.write(b_password + bytes([0]))
    crc_encryption_key = athome_crc(encryption_key)
    crc_encryption_iv = athome_crc(encryption_iv)
    mod.write(struct.pack('<H', crc_encryption_key))
    mod.write(encryption_key)
    mod.write(struct.pack('<H', crc_encryption_iv))
    mod.write(encryption_iv)
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


def set_date_time(mod):
    now = datetime.now()
    date = struct.pack('<BBBBBH', now.second, now.minute, now.hour, now.day, now.month, now.year)
    crc_date = struct.pack('<H', athome_crc(date))
    mod.write(AtHomeProtocol['SetDateTime'].encode('ascii'))
    mod.write(AtHomeProtocol['end_of_line'].encode('ascii'))
    mod.write(crc_date)
    mod.write(date)
    mod.write(AtHomeProtocol['end_of_command'].encode('ascii'))
    return None


AtHomeCommands = {
    'UPLOAD_DATA': upload_data,
    'SET_WIFI': set_wifi,
    'SET_END_POINT': set_end_point,
    'SET_PROFILE': set_profile,
    'SET_DATE_TIME': set_date_time,
}
