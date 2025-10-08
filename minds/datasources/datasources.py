from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel

import minds.exceptions as exc
import minds.utils as utils

if TYPE_CHECKING:
    from minds.client import Client


class Datasource(BaseModel):
    """
    Existed datasource. It is returned by this SDK when datasource is queried from server
    """
    name: str
    engine: str
    description: Optional[str] = None
    connection_data: Optional[dict] = None
    created_at: str
    modified_at: str


class Datasources:
    def __init__(self, client: 'Client'):
        self.api = client.api

    def create(
        self,
        name: str,
        engine: str,
        description: Optional[str] = None,
        connection_data: Optional[dict] = None,
        replace: bool = False,
    ):
        """
        Create new datasource.

        :param name: name of datasource.
        :param engine: type of database handler, for example 'postgres', 'mysql', ...
        :param description: str, optional, description of the database. Used by mind to know what data can be got from it.
        :param connection_data: dict, optional, credentials to connect to database.
        :return: Datasource object.
        """
        utils.validate_datasource_name(name)

        if replace:
            try:
                self.get(name)
                self.drop(name)
            except exc.ObjectNotFound:
                ...

        data = {
            'name': name,
            'engine': engine,
        }
        if connection_data is not None:
            data['connection_data'] = connection_data
        if description is not None:
            data['description'] = description

        response = self.api.post(
            '/datasources',
            data=data
        )
        return Datasource(**response.json())
    
    def update(
        self,
        name: str,
        new_name: Optional[str] = None,
        description: Optional[str] = None,
        connection_data: Optional[dict] = None,
    ):
        """
        Update existing datasource.

        :param name: name of datasource to update.
        :param new_name: new name of datasource.
        :param description: str, optional, description of the database. Used by mind to know what data can be got from it.
        :param connection_data: dict, optional, credentials to connect to database.
        :return: Datasource object.
        """
        utils.validate_datasource_name(name)
        if new_name is not None:
            utils.validate_datasource_name(new_name)

        data = {}
        if new_name is not None:
            data['name'] = new_name
        if connection_data is not None:
            data['connection_data'] = connection_data
        if description is not None:
            data['description'] = description

        response = self.api.put(
            f'/datasources/{name}',
            data=data
        )
        return Datasource(**response.json())

    def list(self) -> List[Datasource]:
        """
        Returns list of datasources

        :return: iterable datasources
        """

        data = self.api.get('/datasources').json()
        ds_list = []
        for item in data:
            ds_list.append(Datasource(**item))
        return ds_list

    def get(self, name: str) -> Datasource:
        """
        Get datasource by name

        :param name: name of datasource
        :return: datasource object
        """

        data = self.api.get(f'/datasources/{name}').json()
        return Datasource(**data)

    def drop(self, name: str):
        """
        Drop datasource by name

        :param name: name of datasource
        """
        self.api.delete(f'/datasources/{name}')
