import os
import copy

api_key = os.getenv('API_KEY')
base_url = 'https://dev.mindsdb.com'

from minds.client import Client

client = Client(api_key, base_url=base_url)

import logging
logging.basicConfig(level=logging.DEBUG)

from minds.datasources.examples import example_ds

from minds.exceptions import ObjectNotFound


def test_datasources():

    # remove previous object
    try:
        client.datasources.drop(example_ds.name)
    except ObjectNotFound:
        ...

    # create
    ds = client.datasources.create(example_ds)
    ds = client.datasources.create(example_ds, replace=True)
    assert ds.name == example_ds.name

    # get
    ds = client.datasources.get(example_ds.name)

    # list
    ds_list = client.datasources.list()
    assert len(ds_list) > 0

    # drop
    client.datasources.drop(ds.name)


def test_minds():
    ds_name2 = 'test_ds_'
    mind_name = 'test_mind_'
    prompt1 = 'answer in german'
    prompt2 = 'answer in spanish'

    # remove previous object
    try:
        client.minds.drop(mind_name)
    except ObjectNotFound:
        ...

    # prepare datasources
    ds = client.datasources.create(example_ds, replace=True)

    # second datasource
    example_ds2 = copy.copy(example_ds)
    example_ds2.name = ds_name2

    # create
    mind = client.minds.create(
        mind_name,
        datasources=[ds],
        provider='openai'
    )
    mind = client.minds.create(
        mind_name,
        replace=True,
        datasources=[ds.name, example_ds2],
        parameters={
            'prompt_template': prompt1
        }
    )

    # get
    mind = client.minds.get(mind_name)
    assert len(mind.datasources) == 2
    assert mind.parameters['prompt_template'] == prompt1

    # list
    mind_list = client.minds.list()
    assert len(mind_list) > 0

    # rename & update
    mind_name2 = 'test_mind2_'
    mind.update(
        name=mind_name2,
        datasources=[ds.name],
        parameters={
            'prompt_template': prompt2
        }
    )
    try:
        mind = client.minds.get(mind_name)
    except ObjectNotFound:
        ...
    else:
        raise Exception('mind is not renamed')

    mind = client.minds.get(mind_name2)
    assert len(mind.datasources) == 1
    assert mind.parameters['prompt_template'] == prompt2

    # add datasource
    mind.add_datasource(example_ds2)
    assert len(mind.datasources) == 2

    # del datasource
    mind.del_datasource(example_ds2.name)
    assert len(mind.datasources) == 1

    # completion
    answer = mind.completion('say hello')
    assert 'hola' in answer.lower()
    # stream completion
    success = False
    for chunk in mind.completion('say hello', stream=True):
        if 'hola' in chunk.content.lower():
            success = True
    assert success is True

    # drop
    client.minds.drop(mind_name)
    client.datasources.drop(example_ds.name)
    client.datasources.drop(ds_name2)
