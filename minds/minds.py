from typing import List, Union
from urllib.parse import urlparse, urlunparse

from openai import OpenAI

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
        self.parameters = parameters
        self.created_at = created_at
        self.updated_at = updated_at

        self.datasources = datasources

    def update(
        self,
        name: str = None,
        model_name: str = None,
        provider=None,
        parameters=None,
        datasources=None
    ):
        data = {}

        if datasources is not None:
            ds_names = []
            for ds in datasources:
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
                ds_names.append(ds)
            data['datasources'] = ds_names

        if name is not None:
            data['name'] = name
        if model_name is not None:
            data['model_name'] = model_name
        if provider is not None:
            data['provider'] = provider
        if parameters is not None:
            data['parameters'] = parameters

        self.api.patch(
            f'/projects/{self.project}/minds/{self.name}',
            data=data
        )
        if name is not None and name != self.name:
            self.name = name

    def add_datasource(self, datasource: Datasource):
        self.api.post(
            f'/projects/{self.project}/minds/{self.name}/datasources',
            data=datasource.model_dump()
        )
        updated = self.client.minds.get(self.name)

        self.datasources = updated.datasources

    def del_datasource(self, datasource: Union[Datasource, str]):
        raise NotImplementedError

    def completion(self, message):
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

        completion = openai_client.chat.completions.create(
            model=self.name,
            messages=[
                {'role': 'user', 'content': message}
            ],
            stream=False
        )
        return completion.choices[0].message.content


class Minds:
    def __init__(self, client):
        self.api = client.api
        self.client = client

        self.project = 'mindsdb'

    def list(self) -> List[Mind]:
        data = self.api.get(f'/projects/{self.project}/minds').json()
        minds_list = []
        for item in data:
            minds_list.append(Mind(self.client, **item))
        return minds_list

    def get(self, name: str) -> Mind:
        item = self.api.get(f'/projects/{self.project}/minds/{name}').json()
        return Mind(self.client, **item)

    def create(
        self, name,
        model_name=None,
        provider=None,
        parameters=None,
        datasources=None,
        replace=False,
    ) -> Mind:

        if replace:
            try:
                self.get(name)
                self.drop(name)
            except exc.ObjectNotFound:
                ...

        ds_names = []
        if datasources:
            for ds in datasources:
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
                ds_names.append(ds)

        if parameters is None:
            parameters = {}
        if 'prompt_template' not in parameters:
            parameters['prompt_template'] = DEFAULT_PROMPT_TEMPLATE

        self.api.post(
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
       self.api.delete(f'/projects/{self.project}/minds/{name}')
