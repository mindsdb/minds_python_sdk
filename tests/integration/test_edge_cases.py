# tests/integration/test_edge_cases.py
import pytest
import time
from minds.client import Client
from minds.exceptions import ObjectNotFound, MindNameInvalid, DatasourceNameInvalid
from tests.integration.utils import get_example_datasource_config


def test_get_and_drop_non_existent_resources(sdk_client: Client):
    """
    Verifies that operating on a non-existent mind or datasource raises ObjectNotFound.
    """
    with pytest.raises(ObjectNotFound):
        sdk_client.minds.get("non_existent_mind")

    with pytest.raises(ObjectNotFound):
        sdk_client.datasources.get("non_existent_ds")

    with pytest.raises(ObjectNotFound):
        sdk_client.minds.drop("non_existent_mind")

    with pytest.raises(ObjectNotFound):
        sdk_client.datasources.drop("non_existent_ds")


def test_update_non_existent_mind(sdk_client: Client):
    """
    Verifies that updating a non-existent mind raises ObjectNotFound.
    """
    with pytest.raises(ObjectNotFound):
        sdk_client.minds.update(name="non_existent_mind", new_name="new_name")


def test_create_with_invalid_names(sdk_client: Client):
    """
    Verifies that creating resources with invalid names raises the correct exceptions.
    """
    # Test invalid mind name
    with pytest.raises(MindNameInvalid):
        sdk_client.minds.create(
            name="invalid-mind-name-123",  # Assuming hyphens are invalid
            datasources=[{"name": "any_ds"}],
            provider="openai",
        )

    # Test invalid datasource name
    invalid_ds_config = get_example_datasource_config(name="invalid-ds-name")
    with pytest.raises(DatasourceNameInvalid):
        sdk_client.datasources.create(**invalid_ds_config)


def test_create_with_replace_flag(request, sdk_client: Client, sdk_datasource):
    """
    Verifies that using replace=True successfully overwrites an existing resource.
    """
    mind_name = f"test_replaceable_mind_{int(time.time())}"

    def finalizer():
        try:
            sdk_client.minds.drop(mind_name)
        except ObjectNotFound:
            # Suppress error if mind was already deleted or never created.
            pass

    request.addfinalizer(finalizer)

    # 1. Create the mind initially with a specific setting
    sdk_client.minds.create(
        name=mind_name,
        datasources=[{"name": sdk_datasource.name}],
        provider="openai",
        parameters={"prompt_template": "first version"},
    )

    # 2. Re-create the same mind with replace=True and a different setting
    mind2 = sdk_client.minds.create(
        name=mind_name,
        replace=True,
        datasources=[{"name": sdk_datasource.name}],
        provider="openai",
        parameters={"prompt_template": "second version"},
    )

    # 3. Verify that the mind has been updated
    assert mind2.name == mind_name
    assert mind2.parameters["prompt_template"] == "second version"
