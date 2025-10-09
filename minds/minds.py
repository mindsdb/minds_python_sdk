from openai import OpenAI
from typing import Dict, List, Optional, Union, Iterable, TYPE_CHECKING

import minds.exceptions as exc
import minds.utils as utils
# from minds.knowledge_bases import KnowledgeBase, KnowledgeBaseConfig

if TYPE_CHECKING:
    from minds.client import Client


class Mind:
    def __init__(
        self,
        client: 'Client',
        name: str,
        model_name: str,
        provider: str,
        # knowledge_bases=None,
        created_at: str,
        modified_at: str,
        status: str,
        datasources: Optional[List[Dict]] = [],
        parameters: Optional[Dict] = {},
        **kwargs
    ):
        self.api = client.api
        self.client = client
        
        self.name = name
        self.model_name = model_name
        self.provider = provider
        self.parameters = parameters if parameters is not None else {}
        self.created_at = created_at
        self.modified_at = modified_at
        self.datasources = datasources
        # self.knowledge_bases = knowledge_bases
        self.status = status

    def __repr__(self):
        return (f'Mind(name={self.name}, '
                f'model_name={self.model_name}, '
                f'provider={self.provider}, '
                f'created_at="{self.created_at}", '
                f'modified_at="{self.modified_at}", '
                f'parameters={self.parameters}, '
                # f'knowledge_bases={self.knowledge_bases}, '
                f'datasources={self.datasources}, '
                f'status={self.status})')

    def add_datasource(self, datasource_name: str, tables: Optional[List[str]] = None) -> None:
        """
        Add an existing Datasource to a Mind.

        :param datasource_name: name of the datasource to add.
        :param tables: list of tables to use from the datasource, optional.
        """
        response = self.api.put(
            f'/minds/{self.name}',
            data={
                'datasources': self.datasources + [{'name': datasource_name, 'tables': tables}]
            }
        )
        updated_mind = response.json()
        self.datasources = updated_mind['datasources']
        self.status = updated_mind['status']

    def remove_datasource(self, datasource_name: str) -> None:
        """
        Remove a datasource from a Mind.

        :param datasource_name: name of the datasource to remove.
        """
        response = self.api.put(
            f'/minds/{self.name}',
            data={
                'datasources': [ds for ds in (self.datasources or []) if ds['name'] != datasource_name]
            }
        )
        updated_mind = response.json()
        self.datasources = updated_mind['datasources']
        self.status = updated_mind['status']

    # def add_knowledge_base(self, knowledge_base: Union[str, KnowledgeBase, KnowledgeBaseConfig]):
    #     """
    #     Add knowledge base to mind
    #     Knowledge base can be passed as
    #      - name, str
    #      - Knowledge base object (minds.knowledge_bases.KnowledgeBase)
    #      - Knowledge base config (minds.knowledge_bases.KnowledgeBaseConfig), in this case knowledge base will be created

    #     :param knowledge_base: input knowledge base
    #     """

    #     kb_name = self.client.minds._check_knowledge_base(knowledge_base)

    #     self.api.post(
    #         f'/projects/{self.project}/minds/{self.name}/knowledge_bases',
    #         data={
    #             'name': kb_name,
    #         }
    #     )
    #     updated = self.client.minds.get(self.name)

    #     self.knowledge_bases = updated.knowledge_bases

    # def del_knowledge_base(self, knowledge_base: Union[KnowledgeBase, str]):
    #     """
    #     Delete knowledge base from mind

    #     Knowledge base can be passed as
    #      - name, str
    #      - KnowledgeBase object (minds.knowledge_bases.KnowledgeBase)

    #     :param knowledge_base: Knowledge base to delete
    #     """
    #     if isinstance(knowledge_base, KnowledgeBase):
    #         knowledge_base = knowledge_base.name
    #     elif not isinstance(knowledge_base, str):
    #         raise ValueError(f'Unknown type of knowledge base: {knowledge_base}')
    #     self.api.delete(
    #         f'/projects/{self.project}/minds/{self.name}/knowledge_bases/{knowledge_base}',
    #     )
    #     updated = self.client.minds.get(self.name)

    #     self.knowledge_bases = updated.knowledge_bases

    def completion(self, message: str, stream: bool = False) -> Union[str, Iterable[str]]:
        """
        Call mind completion

        :param message: input question
        :param stream: to enable stream mode

        :return: string if stream mode is off or iterator of strings if stream mode is on
        """
        openai_client = OpenAI(
            api_key=self.api.api_key,
            base_url=self.api.base_url
        )
        response = openai_client.chat.completions.create(
            model=self.name,
            messages=[
                {'role': 'user', 'content': message}
            ],
            stream=stream
        )
        if stream:
            return self._stream_response(response)
        else:
            return response.choices[0].message.content

    def _stream_response(self, response) -> Iterable[str]:
        for chunk in response:
            yield chunk.choices[0].delta.content


class Minds:
    def __init__(self, client: 'Client'):
        self.api = client.api
        self.client = client

    def list(self) -> List[Mind]:
        """
        Returns list of minds

        :return: iterable
        """
        data = self.api.get(f'/minds').json()
        minds_list = []
        for item in data:
            minds_list.append(Mind(self.client, **item))
        return minds_list

    def get(self, name: str) -> Mind:
        """
        Get mind by name

        :param name: name of the mind
        :return: a mind object
        """
        item = self.api.get(f'/minds/{name}').json()
        return Mind(self.client, **item)

    # def _check_knowledge_base(self, knowledge_base) -> str:
    #     if isinstance(knowledge_base, KnowledgeBase):
    #         knowledge_base = knowledge_base.name
    #     elif isinstance(knowledge_base, KnowledgeBaseConfig):
    #         # if not exists - create
    #         try:
    #             self.client.knowledge_bases.get(knowledge_base.name)
    #         except exc.ObjectNotFound:
    #             self.client.knowledge_bases.create(knowledge_base)

    #         knowledge_base = knowledge_base.name
    #     elif not isinstance(knowledge_base, str):
    #         raise ValueError(f'Unknown type of knowledge base: {knowledge_base}')
    #     return knowledge_base

    def create(
        self,
        name: str,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        datasources: Optional[List[Dict[str, Union[str, List[str]]]]] = None,
        # knowledge_bases=None,
        parameters=None,
        replace=False,
    ) -> Mind:
        """
        Create a new mind and return it

        Datasources should be a list of dicts with keys:
        - name: str
        - tables: Optional[List[str]]

        Knowledge base can be passed as
         - name, str
         - KnowledgeBase object (minds.knowledge_bases.KnowledgeBase)
         - Knowledge base config (minds.knowledge_bases.KnowledgeBaseConfig), in this case knowledge base will be created

        :param name: name of the mind
        :param model_name: llm model name, optional
        :param provider: llm provider, optional
        :param datasources: list of datasources used by mind, optional
        :param knowledge_bases: alter list of knowledge bases used by mind, optional
        :param parameters, dict: other parameters of the mind, optional
        :param replace: if true - to remove existing mind, default is false
        :return: created mind
        """
        utils.validate_mind_name(name)

        if replace:
            try:
                self.get(name)
                self.drop(name)
            except exc.ObjectNotFound:
                ...

        # kb_names = []
        # if knowledge_bases:
        #     for kb in knowledge_bases:
        #         kb = self._check_knowledge_base(kb)
        #         kb_names.append(kb)

        data = {
            'name': name,
            'datasources': datasources or [],
        }
        if model_name:
            data['model_name'] = model_name
        if provider:
            data['provider'] = provider
        if parameters:
            data['parameters'] = parameters
        # if kb_names:
        #     data['knowledge_bases'] = kb_names

        response = self.api.post(
            '/minds',
            data=data
        )

        return Mind(self.client, **response.json())
    
    def update(
        self,
        name: str,
        new_name: Optional[str] = None,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        datasources: Optional[List[Dict[str, Union[str, List[str]]]]] = None,
        parameters: Optional[Dict] = None,
    ) -> Mind:
        """
        Update an existing Mind and return it

        Datasources should be a list of dicts with keys:
        - name: str
        - tables: Optional[List[str]]

        :param name: name of the mind to update
        :param new_name: new name of the mind, optional
        :param model_name: llm model name, optional
        :param provider: llm provider, optional
        :param datasources: list of datasources used by mind, optional
        :param parameters, dict: other parameters of the mind, optional
        :return: updated mind
        """
        utils.validate_mind_name(name)
        if new_name:
            utils.validate_mind_name(new_name)

        data = {}
        if new_name:
            data['name'] = new_name
        if model_name is not None:
            data['model_name'] = model_name
        if provider is not None:
            data['provider'] = provider
        if datasources is not None:
            data['datasources'] = datasources
        if parameters is not None:
            data['parameters'] = parameters

        response = self.api.put(
            f'/minds/{name}',
            data=data
        )

        return Mind(self.client, **response.json())

    def drop(self, name: str) -> None:
       """
       Drop mind by name

       :param name: name of the mind
       """
       self.api.delete(f'/minds/{name}')
