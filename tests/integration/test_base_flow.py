import os
import copy
import pytest

from minds.client import Client

import logging
logging.basicConfig(level=logging.DEBUG)

from minds.datasources.examples import example_ds
from minds.datasources import DatabaseConfig, DatabaseTables

from minds.exceptions import ObjectNotFound, MindNameInvalid, DatasourceNameInvalid


def get_client():
    api_key = os.getenv('MINDS_API_KEY')
    base_url = os.getenv('BASE_URL', 'https://dev.mdb.ai')

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

    valid_ds_name = example_ds.name

    with pytest.raises(DatasourceNameInvalid):
        example_ds.name = "invalid-ds-name"
        client.datasources.create(example_ds)

    example_ds.name = valid_ds_name

    # get
    ds = client.datasources.get(example_ds.name)

    # list
    ds_list = client.datasources.list()
    assert len(ds_list) > 0

    # drop
    client.datasources.drop(ds.name)


def test_minds():
    client = get_client()

    ds_all_name = 'test_datasource_'  # unlimited tables
    ds_rentals_name = 'test_datasource2_'  # limited to home rentals
    mind_name = 'int_test_mind_'
    invalid_mind_name = 'mind-123'
    mind_name2 = 'int_test_mind2_'
    prompt1 = 'answer in spanish'
    prompt2 = 'you are data expert'

    # remove previous objects
    for name in (mind_name, mind_name2):
        try:
            client.minds.drop(name)
        except ObjectNotFound:
            ...

    # prepare datasources
    ds_all_cfg = copy.copy(example_ds)
    ds_all_cfg.name = ds_all_name
    ds_all = client.datasources.create(ds_all_cfg, update=True)

    # second datasource
    ds_rentals_cfg = copy.copy(example_ds)
    ds_rentals_cfg.name = ds_rentals_name
    ds_rentals_cfg.tables = ['home_rentals']

    # create
    with pytest.raises(MindNameInvalid):
        client.minds.create(
            invalid_mind_name,
            datasources=[ds_all],
            provider='openai'
        )
    
    mind = client.minds.create(
        mind_name,
        datasources=[ds_all],
        provider='openai'
    )
    mind = client.minds.create(
        mind_name,
        replace=True,
        datasources=[ds_all.name, ds_rentals_cfg],
        prompt_template=prompt1
    )
    mind = client.minds.create(
        mind_name,
        update=True,
        datasources=[ds_all.name, ds_rentals_cfg],
        prompt_template=prompt1
    )

    # get
    mind = client.minds.get(mind_name)
    assert len(mind.datasources) == 2
    assert mind.prompt_template == prompt1

    # list
    mind_list = client.minds.list()
    assert len(mind_list) > 0

    # completion with prompt 1
    answer = mind.completion('say hello')
    assert 'hola' in answer.lower()

    # rename & update
    mind.update(
        name=mind_name2,
        datasources=[ds_all.name],
        prompt_template=prompt2
    )
    
    with pytest.raises(MindNameInvalid):
        mind.update(
            name=invalid_mind_name,
            datasources=[ds_all.name],
            prompt_template=prompt2
        )
    
    with pytest.raises(ObjectNotFound):
        # this name not exists
        client.minds.get(mind_name)

    mind = client.minds.get(mind_name2)
    assert len(mind.datasources) == 1
    assert mind.prompt_template == prompt2

    # add datasource
    mind.add_datasource(ds_rentals_cfg)
    assert len(mind.datasources) == 2

    # del datasource
    mind.del_datasource(ds_rentals_cfg.name)
    assert len(mind.datasources) == 1

    # ask about data
    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # limit tables
    mind.del_datasource(ds_all.name)
    mind.add_datasource(ds_rentals_name)
    assert len(mind.datasources) == 1

    check_mind_can_see_only_rentals(mind)

    # test ds with limited tables
    ds_all_limited = DatabaseTables(
        name=ds_all_name,
        tables=['home_rentals']
    )
    # mind = client.minds.create(
    #     'mind_ds_limited_',
    #     replace=True,
    #     datasources=[ds_all],
    #     prompt_template=prompt2
    # )
    mind.update(
        name=mind.name,
        datasources=[ds_all_limited],
    )
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
    client.datasources.drop(ds_rentals_cfg.name)

def check_mind_can_see_only_rentals(mind):
    answer = mind.completion('what is max rental price in home rental?')
    assert '5602' in answer.replace(' ', '').replace(',', '')

    # not accessible table
    answer = mind.completion('what is max price in car sales?')
    assert '145000' not in answer.replace(' ', '').replace(',', '')
