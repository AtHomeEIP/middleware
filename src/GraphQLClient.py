import requests


class GraphQLClient():

    class Error(Exception):
        pass

    def __init__(self, api_url):
        self.api_url = api_url

    def send_sample(self, module_id, json_payload, date):
        # TODO check formatting of the parameters before sending calling the API

        module_id = str(module_id)

        # Not using str.format() because JSON ruins it :)
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
        json_post_data %= (date, json_payload, module_id)

        response = requests.post(self.api_url, json={"query": json_post_data})
        if int(response.status_code) != 200:
            raise self.Error("invalid return code from the API: {}".format(response.status_code))


