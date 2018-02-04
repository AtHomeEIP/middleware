import serial, time, serial.tools.list_ports
import glob
import sys


def openUsbArduino():
    """ LIst les ports séries disponible et leurs noms
    :raise EnvironmentError:
        Plateforme inconnue
    :return:
        LAl ist des ports serial dispo sur le système
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/ttyACM*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except OSError:
            pass
    return result


def readDataFromSerial(serial_res):
    i = 0
    for serial_port in serial_res:
        ard = serial.Serial(serial_port)
        while i <= 60:
            data = ard.readline()
            print(data)
            i += 1


def main():
    while 1:
        serial_res = openUsbArduino()
        readDataFromSerial(serial_res)


if __name__ == "__main__":
    main()