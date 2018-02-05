import sys
from Tools import eprint
from ModuleToApiInterface import ModuleToApiInterface

if __name__ == "__main__":
    try:
        moduleInterface = ModuleToApiInterface(api_url="http://woodbox.io:8080/graphql")
        print("running on platform: '{}'".format(sys.platform))
        moduleInterface.main_loop()
    except ModuleToApiInterface.Error as err:
        eprint(err)
        sys.exit(1)
    sys.exit(0)