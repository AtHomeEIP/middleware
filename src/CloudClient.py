import requests
import datetime
import time
from json import loads

class CloudClient():
    """
    Class designed to interact with atHome's GraphQL BoxApi
    Only used to send samples at this moment
    """

    class Error(Exception):
        pass

    modules_types = {
        'Air Quality',
        'Temperature',
        'Humidity',
        'Luminosity'
    }

    def __init__(self, api_url):
        self.api_url = api_url


    def serial_to_mac(self, serial):
        import hashlib
        serialHash = hashlib.md5(str(serial).encode('utf-8')).hexdigest()
        macAddress = ':'.join(format(s, '02x') for s in bytes.fromhex(serialHash))[:17]

    def send_sample(self, module_id, json_payload, date, box_id=2, auth_code='authCodeHashHere'):
        """
        Sends a sample from a module to the BoxApi
        :param module_id: represents the id of the module the sample came from
        :param json_payload: Json String representing the environmental sample
        :param date: DateTime of the sampling, formatted as such: strftime('%Y-%m-%d %H:%M:%S.%f')
        :return: Nothing
        :raises GraphQLClient.Error should an error happen
        """
        # TODO check formatting of the parameters before sending calling the API
        module_id = str(module_id)
        # Using %() instead of str.format() as JSON ruins it because of the {}'s:)
        json_post_data = ''' 
        mutation {
            sendSamples (
                boxAuthCode: "%s"
                boxId: %s
                samples: [{
                    date: "%s"
                    payload: "%s"   
                    moduleId: %s   
            }]){
                nbSentSamples
            }
        }
        '''
        json_payload = json_payload.replace("\"", "\\\"")
        json_post_data %= (auth_code, box_id, date, json_payload, module_id)
        response = requests.post(self.api_url, json={"query": json_post_data})
        # TODO handle other errors: no connection / 200 with error response from the API
        if int(response.status_code) != 200:
            raise self.Error("invalid return code from the API: {}".format(response.status_code))


    def module_exists(self, serial):
        import hashlib
        serialHash = hashlib.md5(str(serial).encode('utf-8')).hexdigest()

        macAddress = ':'.join(format(s, '02x') for s in bytes.fromhex(serialHash))[:17]
        json_post_data = '''
        query{
            getModuleByMac(macAddress:"%s"){
                id
            }
        }        
        '''
        json_post_data %= (macAddress)
        response = requests.post(self.api_url, json={"query": json_post_data})
        if int(response.status_code) == 200:
            data = loads(response.content.decode('utf-8', errors='replace'))
            try:
                return data['data']['getModuleByMac']['id']
            except Exception as err:
                raise NameError("module not found (macAddress: %s)" % (macAddress,))
        else:
            raise NameError(response.reason)


    def new_module(self, Name="Unknown", Type="Unknown", mac="00:00:00:00:00:00"):
        json_post_data = '''
        mutation{
            createModule(moduleInput:{
                mac:"%s"
                name:"%s"
                location:"location"
                type:"%s"
                vendor: "AtHome"
            })
            {
                module {
                    id
                    name
                }

            }
        }
        '''
        json_post_data %= (mac, Name, Type)
        response = requests.post(self.api_url, json={"query": json_post_data})
        if int(response.status_code) == 200:
            data = loads(response.content.decode('utf-8', errors='replace'))
            return data
        else:
            raise NameError(response.reason)

    def assign_module_to_box(self, module_id, module_auth_code='authCodeHashHere', box_id=2, box_auth_code='authCodeHashHere'):
        json_post_data = '''
        mutation{
            assignModuleToBox(boxId:%s, boxAuthCode:"%s", moduleId:%s, moduleAuthCode:"%s"){
                module{
                    box{
                        id
                    }
                }
            }
        }
        '''
        json_post_data %= (box_id, box_auth_code, module_id, module_auth_code)
        response = requests.post(self.api_url, json={"query": json_post_data})
        if int(response.status_code) == 200:
            return loads(response.content.decode('utf-8', errors='replace'))
        else:
            raise NameError(response.reason)


    def send_sample_create_module_if_not_exists(self, serial, sample):
        moduleMacAddress = self.serial_to_mac(serial)



        if not self.module_exists(serial):
            self.new_module()


if __name__ == '__main__':
    client = CloudClient(api_url='https://woodbox.io:1234/graphql')
    client.module_exists(1111)
    1==1