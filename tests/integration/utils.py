from . import config


def get_example_datasource_config(name: str):
    """
    Builds a valid configuration dictionary for creating a datasource.
    """
    base = config.DATASOURCE_CONFIGS[0]

    # Construct a new dictionary with only the keys the API create() method expects.
    # This avoids passing unexpected keyword arguments like 'name_prefix'.
    cfg = {
        "name": name,
        "engine": base["engine"],
        "connection_data": base["connection_data"],
        "description": "A temporary datasource for testing",
    }
    return cfg
