import logging
import pytest
import time
import psycopg2

from minds.client import Client
from minds.exceptions import ObjectNotFound
from . import config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@pytest.fixture(scope="session")
def db_ground_truth():
    """
    Connects directly to the PG database to fetch the true max values for assertions,
    making tests resilient to data changes.
    """
    conn = None
    try:
        # Use a dictionary of connection parameters that psycopg2 expects
        conn_params = {
            "dbname": config.POSTGRES_CONFIG["database"],
            "user": config.POSTGRES_CONFIG["user"],
            "password": config.POSTGRES_CONFIG["password"],
            "host": config.POSTGRES_CONFIG["host"],
            "port": config.POSTGRES_CONFIG["port"],
        }
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        #  Fully qualify the table name with its schema ('demo_data') to resolve the "relation does not exist" error.
        cur.execute("SELECT MAX(rental_price) FROM demo_data.home_rentals;")
        max_rental_price = cur.fetchone()[0]

        cur.close()
        logging.info(
            f"Fetched ground truth from DB: max_rental_price={max_rental_price}"
        )
        return {"max_rental_price": max_rental_price}
    except Exception as e:
        pytest.skip(f"Could not connect to PG database to get ground truth: {e}")
    finally:
        if conn:
            conn.close()


@pytest.fixture(scope="session")
def sdk_client() -> Client:
    """Initialize a Minds Client using centralized config."""
    logging.info(f"Connecting to Minds API at {config.MINDS_API_BASE_URL}")
    client = Client(api_key=config.AUTH_TOKEN, base_url=config.MINDS_API_BASE_URL)
    return client


@pytest.fixture(scope="function")
def sdk_datasource(sdk_client: Client):
    """Creates a temporary datasource for test use and cleans it up."""
    timestamp = str(int(time.time()))[-6:]
    ds_base = config.DATASOURCE_CONFIGS[0]
    ds_name = f"{ds_base['name_prefix']}_{timestamp}"

    ds_config = {
        "name": ds_name,
        "engine": ds_base["engine"],
        "connection_data": ds_base["connection_data"],
        "description": "Temporary test datasource",
    }

    logging.info(f"Creating test datasource {ds_name}")
    ds = sdk_client.datasources.create(**ds_config)

    yield ds  # make datasource available to tests

    # Cleanup
    logging.info(f"Dropping test datasource {ds_name}")
    try:
        sdk_client.datasources.drop(ds_name)
    except ObjectNotFound:
        logging.warning(f"Datasource {ds_name} already removed.")


@pytest.fixture(scope="function")
def sdk_mind(sdk_client: Client, sdk_datasource):
    """Creates a temporary mind for test use and cleans it up."""
    timestamp = int(time.time())
    mind_name = f"test_mind_{timestamp}"

    logging.info(
        f"Creating test mind {mind_name} with datasource {sdk_datasource.name}"
    )
    # Create the mind with 'home_rentals' from the start.
    sdk_client.minds.create(
        mind_name,
        datasources=[{"name": sdk_datasource.name, "tables": ["home_rentals"]}],
        provider="openai",
    )

    yield mind_name

    # Cleanup
    mind_name_upd = f"{mind_name}_upd"
    logging.info(f"Dropping test mind {mind_name_upd}")
    try:
        sdk_client.minds.drop(mind_name_upd)
    except ObjectNotFound:
        # Also try dropping the original name in case the test failed before the update
        try:
            sdk_client.minds.drop(mind_name)
        except ObjectNotFound:
            logging.warning(f"Mind {mind_name} or {mind_name_upd} already removed.")
