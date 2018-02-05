import glob
import sys
import datetime, time
import serial, serial.tools

from GraphQLClient import GraphQLClient
from ModuleTranslator import ModuleTranslator
from Tools import eprint


class ModuleToApiInterface:
    """
    Class used to harvest the raw environmental samples from atHome's modules,
    processing these samples and sending them to the BoxApi.
    """

    class Error(Exception):
        pass

    """ How many lines are read from each module at a time """
    NUMBER_OF_SAMPLES_TO_READ_BY_POLL = 60

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
        """
        Checks if the availables serial ports can be opened, and stores those which can
        into an array for later use.
        :return: Nothing
        :raise ModuleToApiInterface.Error should a serial port not be accessed
        """
        list_of_port_files = self.get_serial_port_file_path_list()
        for port_file in list_of_port_files:
            try:
                s = serial.Serial(port_file)
                s.close()
                self.list_of_serial_ports.append(port_file)
            except serial.SerialException as err:
                raise self.Error("Error while interfacing: {}".format(str(err)))

    def get_serial_port_file_path_list(self):
        """

        :return: An array of Strings containing all available serial ports file paths
        :raises: ModuleToApiInterface.Error if no ports where found OR if the current
        platform is not supported.
        """
        port_serial_file_path_list = []
        if sys.platform.startswith('win'):
            port_serial_file_path_list = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            port_serial_file_path_list = glob.glob('/dev/ttyACM*')
        elif sys.platform.startswith('darwin'):
            port_serial_file_path_list = glob.glob('/dev/tty.*')
        else:
            raise self.Error('Unsupported platform')
        if len(port_serial_file_path_list) == 0:
            raise self.Error("no port file paths found")
        return port_serial_file_path_list

    @staticmethod
    def is_platform_supported(platform):
        """
        determines if a platform is supported or not by this script.
        :param platform: A String representing the name of the current platform
        :return: True if this platform is supported, False otherwise
        """
        return platform in ModuleToApiInterface.SUPPORTED_PLATFORMS

    def read_data_from_this_serial_port(self, serial_port_file_path):
        """
        Reads data from a specific serial port, and sends it to the API.
        :param serial_port_file_path: the file path of the serial port to read from.
        :return: Nothing. Will return the raw read data in the future
        :raises: ModuleToApiInterface.Error should an error happen.
        """
        try:
            serial_descriptor = serial.Serial(serial_port_file_path)
        except serial.SerialException as error:
            raise self.Error(str(error))
        for i in range(self.NUMBER_OF_SAMPLES_TO_READ_BY_POLL):
            raw_module_data = serial_descriptor.readline()
            # TODO Detect module's type. Pollution sensor for now
            three_samples_to_send = ModuleTranslator.raw_module_data_to_json(raw_module_data)
            if three_samples_to_send is not None:
                # TODO parse and format the date to be sent by the module
                date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                # TODO detect the module's ID or MAC address to associate it to the sample
                # 4 is the id of the pollution module in the database
                # TODO separate API calls from this method (semantic/readability fuckup right now)
                try:
                    self.api_client.send_sample(4, three_samples_to_send[0], date)
                    self.api_client.send_sample(4, three_samples_to_send[1], date)
                    self.api_client.send_sample(4, three_samples_to_send[2], date)
                except GraphQLClient.Error as err:
                    raise self.Error(str(err))

    def read_data_from_serial_ports(self):
        """
        Undocumented, as this method will change later.
        As of now, reads data from all the available modules, processes it and sends it to the BoxApi.
        :return:
        """
        serial_port = ""
        try:
            for serial_port in self.list_of_serial_ports:
                # \/ also sends the data to the api, will have to change in the future \/
                self.read_data_from_this_serial_port(serial_port)
                # api calls should be below, like this
                # self.send_sample_to_api(sample)
        except ModuleToApiInterface.Error as error:
            raise self.Error("could not read data from serial port {}: {}".format(serial_port, str(error)))

    def main_loop(self):
        """
        Harvests the raw from the modules,
        process this data so it can be sent to the BoxApi
        sends the processed data to the BoxApi
        :return: Nothing.
        """
        done = False
        while not done:
            # TODO: harvest modules data, format the data, send to the boxapi
            dataSamples = self.read_data_from_serial_ports()


if __name__ == "__main__":

    try:
        moduleInterface = ModuleToApiInterface(api_url="http://woodbox.io:8080/graphql")
        print("running on platform: '{}'".format(sys.platform))
        moduleInterface.main_loop()
    except ModuleToApiInterface.Error as err:
        eprint(err)
        sys.exit(1)
    sys.exit(0)
