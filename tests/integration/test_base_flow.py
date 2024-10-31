import os
import copy
import pytest

from minds.client import Client

import logging
logging.basicConfig(level=logging.DEBUG)

from minds.datasources.examples import example_ds

from minds.exceptions import ObjectNotFound, MindNameInvalid


def get_client():
    api_key = os.getenv('MINDS_API_KEY')
    base_url = os.getenv('MINDS_BASE_URL', 'https://dev.mindsdb.com')

    return Client(api_key, base_url=base_url)


def test_wrong_api_key():
    base_url = 'https://dev.mindsdb.com'
    client = Client('api_key', base_url=base_url)
    with pytest.raises(Exception):
        client.datasources.get('example_db')


def test_datasources():
    client = get_client()

    # remove previous object
    try:
        client.datasources.drop(example_ds.name, force=True)
    except ObjectNotFound:
        ...

    # create
    ds = client.datasources.create(example_ds)
    assert ds.name == example_ds.name
    ds = client.datasources.create(example_ds, update=True)
    assert ds.name == example_ds.name

    # get
    ds = client.datasources.get(example_ds.name)

    # list
    ds_list = client.datasources.list()
    assert len(ds_list) > 0

    # drop
    client.datasources.drop(ds.name)


def test_minds():
    client = get_client()

    ds_name = 'test_datasource_'
    ds_name2 = 'test_datasource2_'
    mind_name = 'int_test_mind_'
    invalid_mind_name = 'mind-123'
    mind_name2 = 'int_test_mind2_'
    prompt1 = 'answer in german'
    prompt2 = 'answer in spanish'

    # remove previous objects
    for name in (mind_name, mind_name2):
        try:
            client.minds.drop(name)
        except ObjectNotFound:
            ...

    # prepare datasources
    ds_cfg = copy.copy(example_ds)
    ds_cfg.name = ds_name
    ds = client.datasources.create(example_ds, replace=True)

    # second datasource
    ds2_cfg = copy.copy(example_ds)
    ds2_cfg.name = ds_name2
    ds2_cfg.tables = ['home_rentals']

    # create
    with pytest.raises(MindNameInvalid):
        mind = client.minds.create(
            invalid_mind_name,
            datasources=[ds],
            provider='openai'
        )
    
    mind = client.minds.create(
        mind_name,
        datasources=[ds],
        provider='openai'
    )
    mind = client.minds.create(
        mind_name,
        replace=True,
        datasources=[ds.name, ds2_cfg],
        prompt_template=prompt1
    )
    mind = client.minds.create(
        mind_name,
        update=True,
        datasources=[ds.name, ds2_cfg],
        prompt_template=prompt1
    )

    # get
    mind = client.minds.get(mind_name)
    assert len(mind.datasources) == 2
    assert mind.prompt_template == prompt1
    
    with pytest.raises(MindNameInvalid):
        client.minds.get(invalid_mind_name)

    # list
    mind_list = client.minds.list()
    assert len(mind_list) > 0

    # rename & update
    mind.update(
        name=mind_name2,
        datasources=[ds.name],
        prompt_template=prompt2
    )
    
    with pytest.raises(MindNameInvalid):
        mind.update(
            name=invalid_mind_name,
            datasources=[ds.name],
            prompt_template=prompt2
        )
    
    with pytest.raises(ObjectNotFound):
        # this name not exists
        client.minds.get(mind_name)

    mind = client.minds.get(mind_name2)
    assert len(mind.datasources) == 1
    assert mind.prompt_template == prompt2

    # add datasource
    mind.add_datasource(ds2_cfg)
    assert len(mind.datasources) == 2

    # del datasource
    mind.del_datasource(ds2_cfg.name)
    assert len(mind.datasources) == 1

    # completion
    answer = mind.completion('say hello')
    assert 'hola' in answer.lower()

    # ask about data
    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # limit tables
    mind.del_datasource(ds.name)
    mind.add_datasource(ds_name2)
    assert len(mind.datasources) == 1

    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # not accessible table
    answer = mind.completion('what is max price in car sales?')
    assert '145000' not in answer.replace(' ', '').replace(',', '')

    # stream completion
    success = False
    for chunk in mind.completion('say hello', stream=True):
        if 'hola' in chunk.content.lower():
            success = True
    assert success is True

    # drop
    client.minds.drop(mind_name2)
    client.datasources.drop(ds.name)
    client.datasources.drop(ds2_cfg.name)
    
    with pytest.raises(MindNameInvalid):
        client.minds.drop(invalid_mind_name)
