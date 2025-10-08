# Minds SDK

> **⚠️ API Version Notice**
>
> This documentation reflects the **current SDK version**, compatible with the **latest Minds Cloud API**.
>
> For users of the **legacy Minds Demo environment** at https://demo.mdb.ai, please refer to the [legacy documentation](README-v1.md) for compatibility.
>
> **Current Version**: v2.x+ (New API for Minds Cloud environments)  
> **Legacy Version**: v1.x ([Legacy Documentation](README-v1.md))

### Installation

To install the SDK, use pip:

```bash
pip install minds-sdk
```

### Getting Started

#### 1. Initialize the Client

To get started, you'll need to initialize the Client with your API key. If you're using a different server, you can also specify a custom base URL.

```python
from minds.client import Client

# Default connection to Minds Cloud
API_KEY = "YOUR_API_KEY"
client = Client(API_KEY)

# Or with custom base URL
BASE_URL = 'https://custom_cloud.mdb.ai/api/v1'
client = Client(API_KEY, base_url=BASE_URL)
```

#### 2. Creating a Datasource

Create a datasource to connect to your database:

```python
# Create datasource
datasource = client.datasources.create(
    name='my_datasource',
    description='House sales data',
    engine='postgres',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    }
)
```

#### 3. Creating a Mind

Create a mind and associate it with your datasource:

```python
# Create mind with datasource
mind = client.minds.create(
    name='mind_name',
    datasources=[
        {
            'name': datasource.name,
            'tables': ['house_sales']
        }
    ]
)

# Or add datasource to existing mind
mind = client.minds.create(name='mind_name')
mind.add_datasource(datasource.name, tables=['house_sales'])
```

#### 4. Wait for Mind to be Ready

Before using your mind, wait for it to complete processing:

```python
import time

def wait_for_mind(mind):
    status = mind.status
    while status != 'COMPLETED':
        print(f'Mind status: {status}')
        time.sleep(3)
        mind = client.minds.get(mind.name)
        status = mind.status
    
        if status == 'FAILED':
            raise Exception('Mind creation failed')

    print('Mind creation successful!')
 
wait_for_mind(mind)
```

### Using Your Mind

#### Chat with OpenAI-Compatible API

You can use the OpenAI client to interact with your minds:

```python
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Chat without streaming
completion = openai_client.chat.completions.create(
    model=mind.name,
    messages=[
        {'role': 'user', 'content': 'How many three-bedroom houses were sold in 2008?'}
    ],
    stream=False
)
print(completion.choices[0].message.content)

# Chat with streaming
completion_stream = openai_client.chat.completions.create(
    model=mind.name,
    messages=[
        {'role': 'user', 'content': 'How many three-bedroom houses were sold in 2008?'}
    ],
    stream=True
)
for chunk in completion_stream:
    print(chunk.choices[0].delta.content)
```

#### Direct Mind Completion

You can also interact directly with the mind:

```python
# Without streaming
response = mind.completion('How many three-bedroom houses were sold in 2008?')
print(response)

# With streaming
for chunk in mind.completion('How many three-bedroom houses were sold in 2008?', stream=True):
    print(chunk)
```

### Managing Minds

#### Create or Replace

Create a new mind or replace an existing one:

```python
mind = client.minds.create(
    name='mind_name',
    datasources=[
        {
            'name': datasource.name,
            'tables': ['home_rentals']
        }
    ],
    replace=True
)
wait_for_mind(mind)
```

#### Update Mind

Update an existing mind:

```python
mind = client.minds.update(
    name='mind_name',  # required
    new_name='new_mind_name',  # optional
    datasources=[  # optional
        {
            'name': datasource.name,
            'tables': ['home_rentals']
        }
    ],
)
wait_for_mind(mind)
```

#### List Minds

Get all your minds:

```python
minds = client.minds.list()
print(minds)
```

#### Get Mind by Name

Retrieve a specific mind:

```python
mind = client.minds.get('mind_name')
```

#### Remove Mind

Delete a mind:

```python
client.minds.drop('mind_name')
```

### Managing Datasources

#### Create or Replace

Create a new datasource or replace an existing one:

```python
datasource = client.datasources.create(
    name='my_datasource',
    description='House sales data',
    engine='postgres',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    },
    replace=True
)
```

#### Update Datasource

Update an existing datasource:

```python
datasource = client.datasources.update(
    name='my_datasource',
    new_name='updated_datasource',
    description='Updated House sales data',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    }
)
```

#### List Datasources

Get all your datasources:

```python
datasources = client.datasources.list()
print(datasources)
```

#### Get Datasource by Name

Retrieve a specific datasource:

```python
datasource = client.datasources.get('my_datasource')
```

#### Remove Datasource

Delete a datasource:

```python
client.datasources.drop('my_datasource')
```
