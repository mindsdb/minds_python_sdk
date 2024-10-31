import re
import minds.exceptions as exc

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
    
