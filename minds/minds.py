from typing import List, Union, Iterable
from urllib.parse import urlparse, urlunparse

from openai import OpenAI
import minds.utils as utils
import minds.exceptions as exc
from minds.datasources import Datasource, DatabaseConfig

DEFAULT_PROMPT_TEMPLATE = 'Use your database tools to answer the user\'s question: {{question}}'


class Mind:
    def __init__(
        self, client, name,
        model_name=None,
        provider=None,
        parameters=None,
        datasources=None,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        self.api = client.api
        self.client = client
        self.project = 'mindsdb'
        
        self.name = name
        self.model_name = model_name
        self.provider = provider
        if parameters is None:
            parameters = {}
        self.prompt_template = parameters.pop('prompt_template', None)
        self.parameters = parameters
        self.created_at = created_at
        self.updated_at = updated_at

        self.datasources = datasources

    def __repr__(self):
        return (f'Mind(name={self.name}, '
                f'model_name={self.model_name}, '
                f'provider={self.provider}, '
                f'created_at="{self.created_at}", '
                f'updated_at="{self.updated_at}", '
                f'parameters={self.parameters}, '
                f'datasources={self.datasources})')

    def update(
        self,
        name: str = None,
        model_name: str = None,
        provider=None,
        prompt_template=None,
        datasources=None,
        parameters=None,
    ):
        """
        Update mind

        If parameter is set it will be applied to mind

        Datasource can be passed as
         - name, str
         - Datasource object (minds.datasources.Database)
         - datasource config (minds.datasources.DatabaseConfig), in this case datasource will be created

        :param name: new name of the mind, optional
        :param model_name: new llm model name, optional
        :param provider: new llm provider, optional
        :param prompt_template: new prompt template, optional
        :param datasources: alter list of datasources used by mind, optional
        :param parameters, dict: alter other parameters of the mind, optional
        """
        data = {}
        
        if name is not None:
            utils.validate_mind_name(name)

        if datasources is not None:
            ds_names = []
            for ds in datasources:
                ds = self.client.minds._check_datasource(ds)
                ds_names.append(ds)
            data['datasources'] = ds_names

        if name is not None:
            data['name'] = name
        if model_name is not None:
            data['model_name'] = model_name
        if provider is not None:
            data['provider'] = provider
        if parameters is None:
            parameters = {}

        data['parameters'] = parameters

        if prompt_template is not None:
            data['parameters']['prompt_template'] = prompt_template

        self.api.patch(
            f'/projects/{self.project}/minds/{self.name}',
            data=data
        )
        if name is not None and name != self.name:
            self.name = name

    def add_datasource(self, datasource: Datasource):
        """
        Add datasource to mind
        Datasource can be passed as
         - name, str
         - Datasource object (minds.datasources.Database)
         - datasource config (minds.datasources.DatabaseConfig), in this case datasource will be created

        :param datasource: input datasource
        """

        ds_name = self.client.minds._check_datasource(datasource)

        self.api.post(
            f'/projects/{self.project}/minds/{self.name}/datasources',
            data={
                'name': ds_name,
            }
        )
        updated = self.client.minds.get(self.name)

        self.datasources = updated.datasources

    def del_datasource(self, datasource: Union[Datasource, str]):
        """
        Delete datasource from mind

        Datasource can be passed as
         - name, str
         - Datasource object (minds.datasources.Database)

        :param datasource: datasource to delete
        """
        if isinstance(datasource, Datasource):
            datasource = datasource.name
        elif not isinstance(datasource, str):
            raise ValueError(f'Unknown type of datasource: {datasource}')
        self.api.delete(
            f'/projects/{self.project}/minds/{self.name}/datasources/{datasource}',
        )
        updated = self.client.minds.get(self.name)

        self.datasources = updated.datasources

    def completion(self, message: str, stream: bool = False) -> Union[str, Iterable[object]]:
        """
        Call mind completion

        :param message: input question
        :param stream: to enable stream mode

        :return: string if stream mode is off or iterator of ChoiceDelta objects (by openai)
        """
        parsed = urlparse(self.api.base_url)

        netloc = parsed.netloc
        if netloc == 'mdb.ai':
            llm_host = 'llm.mdb.ai'
        else:
            llm_host = 'ai.' + netloc

        parsed = parsed._replace(path='', netloc=llm_host)

        base_url = urlunparse(parsed)
        openai_client = OpenAI(
            api_key=self.api.api_key,
            base_url=base_url
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

    def _stream_response(self, response):
        for chunk in response:
            yield chunk.choices[0].delta


class Minds:
    def __init__(self, client):
        self.api = client.api
        self.client = client

        self.project = 'mindsdb'

    def list(self) -> List[Mind]:
        """
        Returns list of minds

        :return: iterable
        """

        data = self.api.get(f'/projects/{self.project}/minds').json()
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
        
        item = self.api.get(f'/projects/{self.project}/minds/{name}').json()
        return Mind(self.client, **item)

    def _check_datasource(self, ds) -> str:
        if isinstance(ds, Datasource):
            ds = ds.name
        elif isinstance(ds, DatabaseConfig):
            # if not exists - create
            try:
                self.client.datasources.get(ds.name)
            except exc.ObjectNotFound:
                self.client.datasources.create(ds)

            ds = ds.name
        elif not isinstance(ds, str):
            raise ValueError(f'Unknown type of datasource: {ds}')
        return ds

    def create(
        self, name,
        model_name=None,
        provider=None,
        prompt_template=None,
        datasources=None,
        parameters=None,
        replace=False,
        update=False,
    ) -> Mind:
        """
        Create a new mind and return it

        Datasource can be passed as
         - name, str
         - Datasource object (minds.datasources.Database)
         - datasource config (minds.datasources.DatabaseConfig), in this case datasource will be created

        :param name: name of the mind
        :param model_name: llm model name, optional
        :param provider: llm provider, optional
        :param prompt_template: instructions to llm, optional
        :param datasources: list of datasources used by mind, optional
        :param parameters, dict: other parameters of the mind, optional
        :param replace: if true - to remove existing mind, default is false
        :param update: if true - to update mind if exists, default is false
        :return: created mind
        """
        
        if name is not None:
            utils.validate_mind_name(name)

        if replace:
            try:
                self.get(name)
                self.drop(name)
            except exc.ObjectNotFound:
                ...

        ds_names = []
        if datasources:
            for ds in datasources:
                ds = self._check_datasource(ds)

                ds_names.append(ds)

        if parameters is None:
            parameters = {}

        if prompt_template is not None:
            parameters['prompt_template'] = prompt_template
        if 'prompt_template' not in parameters:
            parameters['prompt_template'] = DEFAULT_PROMPT_TEMPLATE

        if update:
            method = self.api.put
        else:
            method = self.api.post

        method(
            f'/projects/{self.project}/minds',
            data={
                'name': name,
                'model_name': model_name,
                'provider': provider,
                'parameters': parameters,
                'datasources': ds_names,
            }
        )
        mind = self.get(name)

        return mind

    def drop(self, name: str):
       """
       Drop mind by name

       :param name: name of the mind
       """

       self.api.delete(f'/projects/{self.project}/minds/{name}')
