import re
import minds.exceptions as exc

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
    
