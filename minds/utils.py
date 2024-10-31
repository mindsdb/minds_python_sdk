import re
import minds.exceptions as exc
from urllib.parse import urlparse, urlunparse

def get_openai_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)

    netloc = parsed.netloc
    if netloc == 'mdb.ai':
        llm_host = 'llm.mdb.ai'
    else:
        llm_host = 'ai.' + netloc

    parsed = parsed._replace(path='', netloc=llm_host)

    return urlunparse(parsed)


def validate_mind_name(mind_name):
    """
    Validate the Mind name.

    A valid Mind name should:
    - Start with a letter
    - Contain only letters, numbers, or underscores
    - Have a maximum length of 32 characters
    - Not contain spaces

    Parameters:
    mind_name (str): The Mind name to validate.

    Returns:
    bool: True if valid, False otherwise.
    """
    # Regular expression pattern
    pattern = r'^[A-Za-z][A-Za-z0-9_]{0,31}$'

    # Check if the Mind name matches the pattern
    if not re.match(pattern, mind_name):
        raise exc.MindNameInvalid("Mind name should start with a letter and contain only letters, numbers or underscore, with a maximum of 32 characters. Spaces are not allowed.")


def validate_datasource_name(ds_name):
    """
    Validate the datasource name.

    A valid datasource name should:
    - Start with a letter
    - Contain only letters, numbers, or underscores
    - Have a maximum length of 62 characters
    - Not contain spaces

    Parameters:
    ds_name (str): The datasource name to validate.

    Returns:
    bool: True if valid, False otherwise.
    """
    # Regular expression pattern
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{0,61}$'

    # Check if the datasource name matches the pattern
    if not re.match(pattern, ds_name):
        raise exc.DatasourceNameInvalid("Datasource name should start with a letter and contain only letters, numbers or underscore, with a maximum of 62 characters. Spaces are not allowed.")
