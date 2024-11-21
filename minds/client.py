
from minds.rest_api import RestAPI

from minds.datasources import Datasources
from minds.knowledge_bases import KnowledgeBases
from minds.minds import Minds


class Client:

    def __init__(self, api_key, base_url=None):

        self.api = RestAPI(api_key, base_url)

        self.datasources = Datasources(self)
        self.knowledge_bases = KnowledgeBases(self)

        self.minds = Minds(self)
