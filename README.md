# Minds SDK

### Installation

To install the SDK, use pip:

```bash
pip install minds-sdk
```

### Getting Started

1. Initialize the Client

To get started, you'll need to initialize the Client with your API key. If you're using a different server, you can also specify a custom base URL.

```python
from minds.client import Client

# Default connection to Minds Cloud that uses 'https://mdb.ai' as the base URL
client = Client("YOUR_API_KEY")

# If you have self-hosted Minds Cloud instance, use your custom base URL
base_url = 'https://<custom_cloud>.mdb.ai/'
client = Client("YOUR_API_KEY", base_url)
```

2. Creating a Data Source

You can connect to various databases, such as PostgreSQL, by configuring your data source. Use the DatabaseConfig to define the connection details for your data source.

```python

from minds.datasources import DatabaseConfig

postgres_config = DatabaseConfig(
    name='my_datasource',
    description='<DESCRIPTION-OF-YOUR-DATA>',
    engine='postgres',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    },
    tables=['<TABLE-1>', '<TABLE-2>']
)
```

3. Creating a Mind

You can create a `mind` and associate it with a data source.

```python

# Create a mind with a data source
mind = client.minds.create(name='mind_name', datasources=[postgres_config])

# Alternatively, create a data source separately and add it to a mind later
datasource = client.datasources.create(postgres_config)
mind2 = client.minds.create(name='mind_name', datasources=[datasource])
```

You can also add a data source to an existing mind:

```python

# Create a mind without a data source
mind3 = client.minds.create(name='mind_name')

# Add a data source to the mind
mind3.add_datasource(postgres_config)  # Using the config
mind3.add_datasource(datasource)       # Using the data source object
```

### Managing Minds

You can create a mind or replace an existing one with the same name.

```python

mind = client.minds.create(name='mind_name', replace=True, datasources=[postgres_config])
```

To update a mind, specify the new name and data sources. The provided data sources will replace the existing ones.

```python

mind.update(
    name='mind_name',
    datasources=[postgres_config]
)
```

#### List Minds

You can list all the minds you’ve created.

```python

print(client.minds.list())
```

#### Get a Mind by Name

You can fetch details of a mind by its name.

```python

mind = client.minds.get('mind_name')
```

#### Remove a Mind

To delete a mind, use the following command:

```python

client.minds.drop('mind_name')
```

### Managing Data Sources

To view all data sources:

```python

print(client.datasources.list())
```

#### Get a Data Source by Name

You can fetch details of a specific data source by its name.

```python

datasource = client.datasources.get('my_datasource')
```

#### Remove a Data Source

To delete a data source, use the following command:

```python

client.datasources.drop('my_datasource')
```
>Note: The SDK currently does not support automatically removing a data source if it is no longer connected to any mind.

### Other SDKs
- [Ruby-SDK](https://github.com/tungnt1203/minds_ruby_sdk)
- [Dart-SDK](https://github.com/ArnavK-09/mdb_dart)

#### Command Line Tools
- [Minds CLI](https://github.com/Better-Boy/minds-cli-sdk)


