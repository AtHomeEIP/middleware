import re
import json

class ModuleTranslator:
    """
    Class used to translate the raw data harvested from the modules into
    processed data ready to be sent to the API
    """

    GAS_REGEX = "LPG:([0-9]+)ppm[ \t]+CO:([0-9]+)ppm[ \t]+SMOKE:([0-9]+)ppm"

    def __init__(self):
        pass

    @staticmethod
    def raw_module_data_to_json(raw_data):
        """
        Translates a line from the Gas detection module into a JSON string
        :param raw_data: a raw Bytes line read from the gas module
        :return: either None or an array of JSON Strings containing
        the data ready to be sent to the API
        """
        raw_data = str(raw_data)
        # Remove trailing newline
        raw_data = raw_data[:-1]
        matches = re.search(ModuleTranslator.GAS_REGEX, raw_data)
        # no matches founds / incomplete match
        if matches is None:
            return None
        matches = matches.groups()
        samplesArray = []
        # Petroleum gasses
        lpg_dict = {}
        samplesArray.append(lpg_dict)
        lpg_dict["unit_measure"] = "LPG(ppm)"
        lpg_dict["measure"] = matches[0]
        lpg_dict["name"]    = "pollution"
        # Carbon monoxyde
        co_dict = {}
        samplesArray.append(co_dict)
        co_dict["unit_measure"] = "CO(ppm)"
        co_dict["measure"] = matches[1]
        co_dict["name"]    = "pollution"
        # Smoke
        smoke_dict = {}
        samplesArray.append(smoke_dict)
        smoke_dict["unit_measure"] = "SMOKE(ppm)"
        smoke_dict["measure"] = matches[2]
        smoke_dict["name"]    = "pollution"
        return [json.dumps(x) for x in samplesArray]