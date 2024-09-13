
from minds.datasources import DatabaseConfig

example_ds = DatabaseConfig(
    name='example_ds',
    engine='postgres',
    description='Minds example database',
    connection_data={
        "user": "demo_user",
        "password": "demo_password",
        "host": "samples.mindsdb.com",
        "port": "5432",
        "database": "demo",
        "schema": "demo_data"
    }
)
