import requests
import datetime
import time

class GraphQLClient():
    """
    Class designed to interact with atHome's GraphQL BoxApi
    Only used to send samples at this moment
    """

    class Error(Exception):
        pass

    def __init__(self, api_url):
        self.api_url = api_url

    def send_sample(self, module_id, json_payload, date):
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
            newSample (sample: {
              date: "%s"
              payload: "%s"   
              moduleId: %s   
            }){
              date
              payload
              moduleId
            }
        }
        '''
        json_payload = json_payload.replace("\"", "\\\"")
        json_post_data %= (date, json_payload, module_id)
        response = requests.post(self.api_url, json={"query": json_post_data})
        # TODO handle other errors: no connection / 200 with error response from the API
        if int(response.status_code) != 200:
            raise self.Error("invalid return code from the API: {}".format(response.status_code))


