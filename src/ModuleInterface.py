import glob
import sys
import serial, serial.tools

from .GraphQLClient import GraphQLClient

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

        if not self.is_platform_supported("pootis"):
            raise self.Error("unsupported platform: \'{}\'".format(sys.platform))

        self.api_url = api_url
        self.apiClient = GraphQLClient(self.api_url)

    def is_platform_supported(self, platform):
        for supported_platform in self.SUPPORTED_PLATFORMS:
            if platform.startswith(supported_platform):
                return True
        return False

    def main_loop(self):
        done = False

        while not done:
            # TODO: harvest modules data, format the data, send to the boxapi
            pass

if __name__ == "__main__":

    try:
        moduleInterface = ModuleInterface("http://woodbox.io:8080/graphql")
        print("running on platform: '{}'".format(sys.platform))
        moduleInterface.main_loop()


    except Exception as err:
        eprint(err)
        sys.exit(1)
    sys.exit(0)
