# tests/integration/test_sdk_lifecycle.py
import logging
import time
import pytest
from openai import OpenAI

from minds.client import Client
from tests.integration import config

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants for polling
MIND_COMPLETION_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 15


@pytest.mark.happy_path
def test_sdk_happy_path_lifecycle(
    sdk_client: Client, sdk_mind: str, sdk_datasource, db_ground_truth
):
    """
    Tests the full end-to-end "happy path" lifecycle of minds and datasources.
    This test relies on fixtures from conftest.py for resource setup and teardown.
    """
    # --------------------------------------------------------------------------------
    # 1. Initial State Validation (Mind created with 'home_rentals' by fixture)
    # --------------------------------------------------------------------------------
    mind_name = sdk_mind
    mind = None
    start_time = time.time()

    logging.info(f"Waiting for mind '{mind_name}' to complete processing...")
    while time.time() - start_time < MIND_COMPLETION_TIMEOUT_SECONDS:
        mind = sdk_client.minds.get(mind_name)
        logging.info(f"Polling mind '{mind_name}', current status: {mind.status}")

        if mind.status == "COMPLETED":
            logging.info(f"SUCCESS: Mind '{mind_name}' completed successfully.")
            break
        if mind.status == "FAILED":
            pytest.fail(
                f"Mind '{mind_name}' failed to build. Error: {mind.error_message}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)
    else:
        last_status = mind.status if mind else "UNKNOWN"
        pytest.fail(
            f"Timeout: Mind '{mind_name}' did not complete within "
            f"{MIND_COMPLETION_TIMEOUT_SECONDS} seconds. Last status: '{last_status}'"
        )

    assert mind is not None, "Mind object should exist after polling."
    assert mind.status == "COMPLETED", (
        f"Expected mind status to be COMPLETED, but got {mind.status}."
    )

    # --------------------------------------------------------------------------------
    # 2. Update Mind Name
    # --------------------------------------------------------------------------------
    updated_mind_name = f"{mind_name}_upd"
    sdk_client.minds.update(name=mind_name, new_name=updated_mind_name)

    # --------------------------------------------------------------------------------
    # 3. Test Data-Driven Queries (Home Rentals)
    # --------------------------------------------------------------------------------
    mind = sdk_client.minds.get(updated_mind_name)
    question_rental = "what is max rental price in home_rentals?"
    max_rental_price_str = str(db_ground_truth["max_rental_price"])

    logging.info(f"Testing direct completion for mind '{mind.name}' on home_rentals...")
    answer_rental = mind.completion(question_rental)
    assert max_rental_price_str in answer_rental.replace(",", ""), (
        "Direct completion should return the correct max rental price."
    )
    logging.info(f"Mind completion response: {answer_rental}")

    # Test that the mind CANNOT see tables it wasn't trained on
    question_cars = "what is max price in car_sales?"
    logging.info("Querying mind for car sales data (should not be accessible)...")
    answer_cars = mind.completion(question_cars)
    assert "145000" not in answer_cars.replace(",", ""), (
        "Mind should not have access to car_sales table."
    )

    # --------------------------------------------------------------------------------
    # 4. Test OpenAI-Compatible Chat
    # --------------------------------------------------------------------------------
    logging.info(f"Testing OpenAI-compatible chat for mind '{mind.name}'...")
    # FIX: The OpenAI-compatible endpoint is hosted at /api/v1, not /api/v1/openai.
    openai_base_url = f"{config.MINDS_API_BASE_URL.strip('/')}/api/v1"
    openai_client = OpenAI(api_key=config.AUTH_TOKEN, base_url=openai_base_url)

    completion = openai_client.chat.completions.create(
        model=mind.name,
        messages=[{"role": "user", "content": question_rental}],
        stream=False,
    )
    chat_answer = completion.choices[0].message.content
    assert max_rental_price_str in chat_answer.replace(",", ""), (
        "OpenAI chat should return the correct max rental price."
    )

    # NOTE: The fixtures in conftest.py will handle the final cleanup.
