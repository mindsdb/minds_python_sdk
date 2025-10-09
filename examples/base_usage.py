import time

from openai import OpenAI

from minds.client import Client


# Basic Setup and Workflow

# connect
API_KEY = "YOUR_API_KEY"
BASE_URL = 'https://custom_cloud.mdb.ai/api/v1'  # optional, if you use custom server

client = Client(API_KEY)

# or with custom base URL
client = Client(API_KEY, base_url=BASE_URL)

# create Datasource
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

# create Mind
mind = client.minds.create(
    name='mind_name',
    datasources=[
		{
			'name': datasource.name,
			'tables': ['house_sales']
		}
	]
)

# or add to existing Mind
mind = client.minds.create(name='mind_name')
mind.add_datasource(datasource.name, tables=['house_sales'])

# wait until Mind is ready
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

# chat with the Mind using the OpenAI-compatible Completions API (without streaming)
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

completion = openai_client.chat.completions.create(
    model=mind.name,
    messages=[
        {'role': 'user', 'content': 'How many three-bedroom houses were sold in 2008?'}
    ],
    stream=False
)
print(completion.choices[0].message.content)

# with streaming
completion_stream = openai_client.chat.completions.create(
	model=mind.name,
	messages=[
		{'role': 'user', 'content': 'How many three-bedroom houses were sold in 2008?'}
	],
	stream=True
)
for chunk in completion_stream:
	print(chunk.choices[0].delta.content)

# or chat with the Mind directly (without streaming)
response = mind.completion('How many three-bedroom houses were sold in 2008?')
print(response)

# with streaming
for chunk in mind.completion('How many three-bedroom houses were sold in 2008?', stream=True):
	print(chunk)


# Mind Management

# create or replace
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

# update
mind = client.minds.update(
	name='mind_name', # required
	new_name='new_mind_name', # optional
	datasources=[  # optional
		{
			'name': datasource.name,
			'tables': ['home_rentals']
		}
	],
)
wait_for_mind(mind)

# list
minds = client.minds.list()

# get
mind = client.minds.get('mind_name')

# remove
client.minds.drop('mind_name')

# Datasource Management

# create or replace
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

# update
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

# list
datasources = client.datasources.list()

# get
datasource = client.datasources.get('my_datasource')

# remove
client.datasources.drop('my_datasource')
