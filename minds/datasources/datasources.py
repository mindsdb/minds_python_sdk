from typing import List, Optional, Union

from pydantic import BaseModel, Field

import minds.exceptions as exc

class DatabaseConfig(BaseModel):

    name: str
    engine: str
    description: str
    connection_data: Union[dict, None] = {}
    tables: Union[List[str], None] = []


class Datasource(DatabaseConfig):
    ...

class Datasources:
    def __init__(self, client):
        self.api = client.api

    def create(self, ds_config: DatabaseConfig, replace=False):
        name = ds_config.name

        if replace:
            try:
                self.get(name)
                self.drop(name)
            except exc.ObjectNotFound:
                ...

        self.api.post('/datasources', data=ds_config.model_dump())
        return self.get(name)

    def list(self) -> List[Datasource]:
        data = self.api.get('/datasources').json()
        ds_list = []
        for item in data:
            # TODO skip not sql skills
            if item.get('engine') is None:
                continue
            ds_list.append(Datasource(**item))
        return ds_list

    def get(self, name: str) -> Datasource:
        data = self.api.get(f'/datasources/{name}').json()

        # TODO skip not sql skills
        if data.get('engine') is None:
            raise exc.ObjectNotSupported(f'Wrong type of datasource: {name}')
        return Datasource(**data)

    def drop(self, name: str):
        self.api.delete(f'/datasources/{name}')
