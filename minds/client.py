
from minds.rest_api import RestAPI

from minds.datasources import Datasources
from minds.minds import Minds, OSMinds


class Client:

    def __init__(self, api_key=None, base_url=None, version='v1'):

        self.api = RestAPI(api_key, base_url, version)

        # If no API key is provided, this means we are using MindsDB Server
        if not api_key:
            version = 'os' # open source version
        self.version = version
        self.datasources = Datasources(self)

        if version == 'os':
            self.minds = OSMinds(self)
        else:
            self.minds = Minds(self)

    def __repr__(self):
        return f'Client(api_key={self.api.api_key}, base_url={self.api.base_url}, version={self.version})'
