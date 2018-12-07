#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from middleware_common import *
from OldMiddleWare import parse_command
import sys
import time

if __name__ == "__main__":
    a = QCoreApplication(sys.argv)
    serial_port = QSerialPort()
    serial_port.setPortName(sys.argv[1])
    serial_port.setBaudRate(QSerialPort.Baud9600, QSerialPort.AllDirections)
    serial_port.setParity(QSerialPort.NoParity)
    serial_port.setStopBits(QSerialPort.OneStop)
    serial_port.setDataBits(QSerialPort.Data8)
    serial_port.setFlowControl(QSerialPort.NoFlowControl)
    serial_port.open(QSerialPort.ReadWrite)
    time.sleep(3)
    set_profile(serial_port, 1)
    set_date_time(serial_port)
    set_wifi(serial_port)
    set_end_point(serial_port)
    time.sleep(3)
    while True:
        parse_command(serial_port)
    