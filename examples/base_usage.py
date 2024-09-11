from minds.client import Client

# --- connect ---
client = Client("YOUR_API_KEY")

# or use not default server
base_url = 'https://custom_cloud.mdb.ai/'
client = Client("YOUR_API_KEY", base_url)


# create datasource
from client.datasources import DatabaseConfig

postgres_config = DatabaseConfig(
    name='my_datasource',
	description='<DESCRIPTION-OF-YOUR-DATA>',
	type='postgres',
	connection_args={
    	'user': 'demo_user',
    	'password': 'demo_password',
    	'host': 'samples.mindsdb.com',
    	'port': 5432,
    	'database': 'demo',
    	'schema': 'demo_data'
	},
	tables=['<TABLE-1>', '<TABLE-2>']
)

# create mind
# with datasource at the same time
mind = client.minds.create(name='mind_name', datasources=[postgres_config] )

# or separately
datasource = client.datasources.create(postgres_config)
mind2 = client.minds.create(name='mind_name', datasources=[datasource] )

# or add to existed mind
mind3 = client.minds.create(name='mind_name')
# by config
mind2.add_datasource(postgres_config)
# or by datasource
mind2.add_datasource(datasource)


# --- managing minds ---

# create or replace
mind = client.minds.create(name='mind_name', replace=True, datasources=[postgres_config] )

# update
mind.update(
	name='mind_name', # is required
	datasources=[postgres_config]  # it will replace current datasource list
)

# list
print(client.minds.list())

# get by name
mind = client.minds.get('mind_name')

# removing datasource
# ? should it drop datasource if it is not connected to any mind anymore?
mind.del_datasource(datasource)

# remove mind
client.minds.drop('mind_name')


# --- managing datasources ---

# list
print(client.datasources.list())

# get
datasource = client.datasources.get('my_datasource')

# remove
client.datasources.drop('my_datasource')


