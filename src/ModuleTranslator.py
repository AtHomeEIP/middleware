import re
import json

class ModuleTranslator:

    GAS_REGEX = "LPG:([0-9]+)ppm[ \t]+CO:([0-9]+)ppm[ \t]+SMOKE:([0-9]+)ppm"

    def __init__(self):
        pass

    @staticmethod
    def jsonEncodeData(data):
        data = str(data)
        data = data[:-1]
        matches = re.search(ModuleTranslator.GAS_REGEX, data)
        # no matches founds / incomplete match
        if matches is None:
            return None
        matches = matches.groups()
        samplesArray = []
        lpg_dict = {}
        samplesArray.append(lpg_dict)

        lpg_dict["unit_measure"] = "LPG(ppm)"
        lpg_dict["measure"] = matches[0]
        lpg_dict["name"]    = "pollution"

        co_dict = {}
        samplesArray.append(co_dict)
        co_dict["unit_measure"] = "CO(ppm)"
        co_dict["measure"] = matches[1]
        co_dict["name"]    = "pollution"


        smoke_dict = {}
        samplesArray.append(smoke_dict)
        smoke_dict["unit_measure"] = "SMOKE(ppm)"
        smoke_dict["measure"] = matches[2]
        smoke_dict["name"]    = "pollution"

        return [json.dumps(x) for x in samplesArray]