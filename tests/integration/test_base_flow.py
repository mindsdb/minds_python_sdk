import os
import pytest

from minds.client import Client
from minds.exceptions import ObjectNotFound, MindNameInvalid, DatasourceNameInvalid

import logging
logging.basicConfig(level=logging.DEBUG)


# TODO: Validate these tests and ensure coverage


def get_client():
    api_key = os.getenv('MINDS_API_KEY')
    base_url = os.getenv('BASE_URL', 'https://dev.mdb.ai')

    return Client(api_key, base_url=base_url)


def get_example_datasource_config():
    """Get example datasource configuration parameters"""
    return {
        'name': 'example_ds',
        'engine': 'postgres',
        'description': 'Minds example database',
        'connection_data': {
            "user": "demo_user",
            "password": "demo_password",
            "host": "samples.mindsdb.com",
            "port": "5432",
            "database": "demo",
            "schema": "demo_data"
        }
    }


def test_wrong_api_key():
    base_url = 'https://dev.mdb.ai'
    client = Client('api_key', base_url=base_url)
    # with pytest.raises(Exception):
    client.datasources.get('example_db')


def test_datasources():
    client = get_client()
    example_ds_config = get_example_datasource_config()

    # remove previous object
    try:
        client.datasources.drop(example_ds_config['name'])
    except ObjectNotFound:
        ...

    # create
    ds = client.datasources.create(**example_ds_config)
    assert ds.name == example_ds_config['name']
    
    # create with replace
    ds = client.datasources.create(**example_ds_config, replace=True)
    assert ds.name == example_ds_config['name']

    # test invalid datasource name
    with pytest.raises(DatasourceNameInvalid):
        invalid_config = example_ds_config.copy()
        invalid_config['name'] = "invalid-ds-name"
        client.datasources.create(**invalid_config)

    # get
    ds = client.datasources.get(example_ds_config['name'])

    # list
    ds_list = client.datasources.list()
    assert len(ds_list) > 0

    # drop
    client.datasources.drop(ds.name)


def test_minds():
    client = get_client()
    example_ds_config = get_example_datasource_config()

    ds_all_name = 'test_datasource_'  # unlimited tables
    ds_rentals_name = 'test_datasource2_'  # limited to home rentals
    mind_name = 'int_test_mind_'
    invalid_mind_name = 'mind-123'
    mind_name2 = 'int_test_mind2_'

    # remove previous objects
    for name in (mind_name, mind_name2):
        try:
            client.minds.drop(name)
        except ObjectNotFound:
            ...

    # prepare datasources
    ds_all_config = example_ds_config.copy()
    ds_all_config['name'] = ds_all_name
    ds_all = client.datasources.create(**ds_all_config, replace=True)

    # second datasource  
    ds_rentals_config = example_ds_config.copy()
    ds_rentals_config['name'] = ds_rentals_name
    # Note: In the new API, tables are specified when adding datasource to mind, not when creating datasource

    # create mind with invalid name should fail
    with pytest.raises(MindNameInvalid):
        client.minds.create(
            invalid_mind_name,
            datasources=[{'name': ds_all.name}],
            provider='openai'
        )
    
    # create mind
    mind = client.minds.create(
        mind_name,
        datasources=[{'name': ds_all.name}],
        provider='openai'
    )
    
    # create mind with replace
    mind = client.minds.create(
        mind_name,
        replace=True,
        datasources=[
            {'name': ds_all.name}, 
            {'name': ds_rentals_name, 'tables': ['home_rentals']}
        ]
    )

    # Create the second datasource that will be used later
    ds_rentals = client.datasources.create(**ds_rentals_config, replace=True)

    # get
    mind = client.minds.get(mind_name)
    assert len(mind.datasources) == 2

    # list
    mind_list = client.minds.list()
    assert len(mind_list) > 0

    # completion test
    answer = mind.completion('say hello')
    assert len(answer) > 0  # Just check that we get a response

    # rename & update using client.minds.update
    updated_mind = client.minds.update(
        name=mind_name,
        new_name=mind_name2,
        datasources=[{'name': ds_all.name}]
    )
    assert updated_mind.name == mind_name2
    assert len(updated_mind.datasources) == 1
    
    with pytest.raises(MindNameInvalid):
        client.minds.update(
            name=mind_name2,
            new_name=invalid_mind_name,
            datasources=[{'name': ds_all.name}]
        )
    
    with pytest.raises(ObjectNotFound):
        # this name not exists
        client.minds.get(mind_name)

    mind = client.minds.get(mind_name2)
    assert len(mind.datasources) == 1

    # add datasource
    mind.add_datasource(ds_rentals.name)
    assert len(mind.datasources) == 2

    # remove datasource
    mind.remove_datasource(ds_rentals.name)
    assert len(mind.datasources) == 1

    # ask about data
    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # limit tables
    mind.remove_datasource(ds_all.name)
    mind.add_datasource(ds_rentals.name, tables=['home_rentals'])
    assert len(mind.datasources) == 1

    check_mind_can_see_only_rentals(mind)

    # test ds with limited tables - use client.minds.update instead of DatabaseTables
    client.minds.update(
        name=mind.name,
        datasources=[{'name': ds_all.name, 'tables': ['home_rentals']}]
    )
    mind = client.minds.get(mind.name)  # refresh mind object
    check_mind_can_see_only_rentals(mind)

    # stream completion
    success = False
    for chunk in mind.completion('what is max rental price in home rental?', stream=True):
        if '5602' in chunk.content.lower():
            success = True
    assert success is True

    # drop
    client.minds.drop(mind_name2)
    client.datasources.drop(ds_all.name)
    client.datasources.drop(ds_rentals.name)

def check_mind_can_see_only_rentals(mind):
    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # not accessible table
    answer = mind.completion('what is max price in car sales?')
    assert '145000' not in answer.replace(' ', '').replace(',', '')
