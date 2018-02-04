import glob
import sys
import serial, serial.tools

from GraphQLClient import GraphQLClient

from Tools import eprint


class ModuleInterface:
    class Error(Exception):
        pass

    SUPPORTED_PLATFORMS = [
        "win"
        , "linux"
        , "cygwin"
        , "darwin"
    ]

    def __init__(self, api_url):
        if not self.is_platform_supported(sys.platform):
            raise self.Error("unsupported platform: \'{}\'".format(sys.platform))
        self.api_url = api_url
        self.api_client = GraphQLClient(self.api_url)
        self.list_of_serial_ports = []
        self.scan_serial_ports()

    def scan_serial_ports(self):
        list_of_port_files = self.get_serial_port_file_path_list()
        for port_file in list_of_port_files:
            try:
                s = serial.Serial(port_file)
                s.close()
                self.list_of_serial_ports.append(port_file)
            except OSError as err:
                raise self.Error("Error while interfacing: {}".format(str(err)))

    def get_serial_port_file_path_list(self):
        port_serial_file_path_list = None
        if sys.platform.startswith('win'):
            port_serial_file_path_list = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            port_serial_file_path_list = glob.glob('/dev/ttyACM*')
        elif sys.platform.startswith('darwin'):
            port_serial_file_path_list = glob.glob('/dev/tty.*')
        else:
            raise self.Error('Unsupported platform')
        if len(port_serial_file_path_list) == 0:
            raise self.Error("no port file found")
        return port_serial_file_path_list

    def is_platform_supported(self, platform):
        for supported_platform in self.SUPPORTED_PLATFORMS:
            if platform.startswith(supported_platform):
                return True
        return False

    def read_data_from_serial_ports(self):
        serial_port = ""
        try:
            for serial_port in self.list_of_serial_ports:
                ard = serial.Serial(serial_port)
                i = 0
                while i <= 60:
                    data = ard.readline()
                    print(data)
                    i += 1
        except OSError as err:
            raise self.Error("could not read data from serial port {}: {}".format(serial_port, str(err)))

    def main_loop(self):
        done = False

        while not done:
            # TODO: harvest modules data, format the data, send to the boxapi
            dataSamples = self.read_data_from_serial_ports()
            pass


if __name__ == "__main__":

    try:
        moduleInterface = ModuleInterface("http://woodbox.io:8080/graphql")
        print("running on platform: '{}'".format(sys.platform))
        moduleInterface.main_loop()


    except ModuleInterface.Error as err:
        eprint(err)
        sys.exit(1)
    sys.exit(0)
