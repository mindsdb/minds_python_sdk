
from unittest.mock import Mock
from unittest.mock import patch
import pytest

from minds import rest_api
from minds.client import Client
from minds.datasources import Datasource
# from minds.knowledge_bases import EmbeddingConfig, KnowledgeBaseConfig, VectorStoreConfig


# patch _raise_for_status for testing
rest_api._raise_for_status = Mock()


@pytest.fixture
def minds_client():
    """Test client instance"""
    return Client('1234567890abc')


@pytest.fixture
def example_ds():
    """Example datasource object (as would be returned from the API)"""
    return Datasource(
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
        },
        created_at='2024-01-01T00:00:00Z',
        modified_at='2024-01-01T00:00:00Z'
    )
    
    
def response_mock(mock, data):
    def side_effect(*args, **kwargs):
        r_mock = Mock()
        r_mock.status_code = 200
        r_mock.json.return_value = data
        return r_mock
    mock.side_effect = side_effect


class TestDatasources:

    def _compare_ds(self, ds1, ds2):
        assert ds1.name == ds2.name
        assert ds1.engine == ds2.engine
        assert ds1.description == ds2.description
        assert ds1.connection_data == ds2.connection_data
        # Note: tables field removed from current Datasource model

    @patch('requests.get')
    @patch('requests.post')
    def test_create_datasources(self, mock_post, mock_get, minds_client, example_ds):
        response_mock(mock_post, example_ds.model_dump())  # POST response for create
        response_mock(mock_get, example_ds.model_dump())   # GET response for replace check

        # Extract config data from example_ds for create call
        ds_config = {
            'name': example_ds.name,
            'engine': example_ds.engine,
            'description': example_ds.description,
            'connection_data': example_ds.connection_data
        }

        ds = minds_client.datasources.create(**ds_config)

        def check_ds_created(ds, mock_method, url):
            self._compare_ds(ds, example_ds)
            args, kwargs = mock_method.call_args

            assert kwargs['headers'] == {'Authorization': 'Bearer 1234567890abc', 'Content-Type': 'application/json'}
            assert kwargs['json'] == ds_config
            assert args[0] == url

        check_ds_created(ds, mock_post, 'https://mdb.ai/api/v1/datasources')

        # with replace (should still use POST after delete)
        ds = minds_client.datasources.create(**ds_config, replace=True)
        check_ds_created(ds, mock_post, 'https://mdb.ai/api/v1/datasources')

    @patch('requests.get')
    def test_get_datasource(self, mock_get, minds_client, example_ds):
        response_mock(mock_get, example_ds.model_dump())
        ds = minds_client.datasources.get(example_ds.name)
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/v1/datasources/{example_ds.name}')

    @patch('requests.delete')
    def test_delete_datasource(self, mock_del, minds_client):
        minds_client.datasources.drop('ds_name')

        args, _ = mock_del.call_args
        assert args[0].endswith('/api/v1/datasources/ds_name')

    @patch('requests.get')
    def test_list_datasources(self, mock_get, minds_client, example_ds):
        response_mock(mock_get, [example_ds.model_dump()])
        ds_list = minds_client.datasources.list()
        assert len(ds_list) == 1
        ds = ds_list[0]
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/v1/datasources')


# class TestKnowledgeBases:

#     def _compare_knowledge_base(self, knowledge_base, config):
#         assert knowledge_base.name == config.name

#     @patch('requests.get')
#     @patch('requests.post')
#     def test_create_knowledge_bases(self, mock_post, mock_get):
#         client = get_client()

#         test_embedding_config = EmbeddingConfig(
#             provider='openai',
#             model='gpt-4o',
#             params={
#                 'k1': 'v1'
#             }
#         )
#         test_vector_store_connection_data = {
#             'user': 'test_user',
#             'password': 'test_password',
#             'host': 'boop.mindsdb.com',
#             'port': '5432',
#             'database': 'test',
#         }
#         test_vector_store_config = VectorStoreConfig(
#             engine='pgvector',
#             connection_data=test_vector_store_connection_data,
#             table='test_table'
#         )
#         test_knowledge_base_config = KnowledgeBaseConfig(
#             name='test_kb',
#             description='Test knowledge base',
#             vector_store_config=test_vector_store_config,
#             embedding_config=test_embedding_config,
#             params={
#                 'k1': 'v1'
#             }
#         )
#         response_mock(mock_get, test_knowledge_base_config.model_dump())

#         created_knowledge_base = client.knowledge_bases.create(test_knowledge_base_config)
#         self._compare_knowledge_base(created_knowledge_base, test_knowledge_base_config)

#         args, kwargs = mock_post.call_args

#         assert kwargs['headers'] == {'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'}

#         expected_create_request = {
#             'name': test_knowledge_base_config.name,
#             'description': test_knowledge_base_config.description,
#             'vector_store': {
#                 'engine': test_vector_store_config.engine,
#                 'connection_data': test_vector_store_config.connection_data,
#                 'table': test_vector_store_config.table
#             },
#             'embedding_model': {
#                 'provider': test_embedding_config.provider,
#                 'name': test_embedding_config.model,
#                 'k1': 'v1'
#             },
#             'params': {
#                 'k1': 'v1'
#             }
#         }

#         assert kwargs['json'] == expected_create_request
#         assert args[0] == 'https://mdb.ai/api/knowledge_bases'

#     @patch('requests.get')
#     def test_get_knowledge_base(self, mock_get):
#         client = get_client()

#         test_embedding_config = EmbeddingConfig(
#             provider='openai',
#             model='gpt-4o',
#             params={
#                 'k1': 'v1'
#             }
#         )
#         test_vector_store_connection_data = {
#             "user": "test_user",
#             "password": "test_password",
#             "host": "boop.mindsdb.com",
#             "port": "5432",
#             "database": "test",
#         }
#         test_vector_store_config = VectorStoreConfig(
#             engine='pgvector',
#             connection_data=test_vector_store_connection_data,
#             table='test_table'
#         )
#         test_knowledge_base_config = KnowledgeBaseConfig(
#             name='test_kb',
#             description='Test knowledge base',
#             vector_store_config=test_vector_store_config,
#             embedding_config=test_embedding_config
#         )

#         # Expected response from MindsDB API server.
#         get_response = {
#             'created_at': '2024-11-15',
#             'embedding_model': 'test_kb_embeddings',
#             'id': 1,
#             'name': 'test_kb',
#             'params': {},
#             'project_id': 1,
#             'updated_at': '2024-11-15',
#             'vector_database': 'test_kb_vector_store',
#             'vector_database_table': 'test_table'
#         }
#         response_mock(mock_get, get_response)
#         get_knowledge_base = client.knowledge_bases.get(test_knowledge_base_config.name)
#         self._compare_knowledge_base(get_knowledge_base, test_knowledge_base_config)

#         args, _ = mock_get.call_args
#         assert args[0].endswith(f'/api/knowledge_bases/{test_knowledge_base_config.name}')

#     @patch('requests.delete')
#     def test_delete_knowledge_base(self, mock_del):
#         client = get_client()

#         client.knowledge_bases.drop('test_kb')

#         args, _ = mock_del.call_args
#         assert args[0].endswith('/api/knowledge_bases/test_kb')

#     @patch('requests.get')
#     def test_list_knowledge_bases(self, mock_get):
#         client = get_client()

#         test_embedding_config = EmbeddingConfig(
#             provider='openai',
#             model='gpt-4o',
#             params={
#                 'k1': 'v1'
#             }
#         )
#         test_vector_store_connection_data = {
#             "user": "test_user",
#             "password": "test_password",
#             "host": "boop.mindsdb.com",
#             "port": "5432",
#             "database": "test",
#         }
#         test_vector_store_config = VectorStoreConfig(
#             engine='pgvector',
#             connection_data=test_vector_store_connection_data,
#             table='test_table'
#         )
#         test_knowledge_base_config = KnowledgeBaseConfig(
#             name='test_kb',
#             description='Test knowledge base',
#             vector_store_config=test_vector_store_config,
#             embedding_config=test_embedding_config
#         )

#         # Expected response from MindsDB API server.
#         get_response = {
#             'created_at': '2024-11-15',
#             'embedding_model': 'test_kb_embeddings',
#             'id': 1,
#             'name': 'test_kb',
#             'params': {},
#             'project_id': 1,
#             'updated_at': '2024-11-15',
#             'vector_database': 'test_kb_vector_store',
#             'vector_database_table': 'test_table'
#         }
#         response_mock(mock_get, [get_response])
#         knowledge_base_list = client.knowledge_bases.list()
#         assert len(knowledge_base_list) == 1
#         knowledge_base = knowledge_base_list[0]
#         self._compare_knowledge_base(knowledge_base, test_knowledge_base_config)

#         args, _ = mock_get.call_args
#         assert args[0].endswith('/api/knowledge_bases')


class TestMinds:

    mind_json = {
        'model_name': 'gpt-4o',
        'name': 'test_mind',
        'datasources': [{'name': 'example_ds'}],
        'provider': 'openai',
        'parameters': {
            'prompt_template': "Answer the user's question"
        },
        'created_at': 'Thu, 26 Sep 2024 13:40:57 GMT',
        'modified_at': 'Thu, 26 Sep 2024 13:40:57 GMT',
        'status': 'COMPLETED'
    }

    def _compare_mind(self, mind, mind_json):
        assert mind.name == mind_json['name']
        assert mind.model_name == mind_json['model_name']
        assert mind.provider == mind_json['provider']
        assert mind.parameters == mind_json['parameters']

    @patch('requests.get')
    @patch('requests.post')
    @patch('requests.delete')
    def test_create(self, mock_del, mock_post, mock_get, minds_client):
        mind_name = 'test_mind'
        prompt_template = 'always agree'
        datasources = [{'name': 'my_ds'}]
        provider = 'openai'

        response_mock(mock_post, self.mind_json)
        create_params = {
            'name': mind_name,
            'parameters': {'prompt_template': prompt_template},
            'datasources': datasources,
            'provider': provider
        }
        mind = minds_client.minds.create(**create_params)

        def check_mind_created(mind, mock_method, create_params, url):
            args, kwargs = mock_method.call_args
            assert args[0].endswith(url)
            request = kwargs['json']
            
            # Check basic fields
            assert request['name'] == create_params['name']
            if 'datasources' in create_params:
                assert request['datasources'] == create_params['datasources']
            if 'provider' in create_params:
                assert request['provider'] == create_params['provider']
            if 'parameters' in create_params:
                assert request['parameters'] == create_params['parameters']

            self._compare_mind(mind, self.mind_json)

        check_mind_created(mind, mock_post, create_params, '/api/v1/minds')

        # -- with replace --
        create_params = {
            'name': mind_name,
            'parameters': {'prompt_template': prompt_template},
            'provider': provider,
        }
        
        # Mock the GET request for checking if mind exists (for replace)
        response_mock(mock_get, self.mind_json)
        
        mind = minds_client.minds.create(replace=True, **create_params)

        # was deleted
        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/v1/minds/{mind_name}')

        check_mind_created(mind, mock_post, create_params, '/api/v1/minds')

    @patch('requests.get')
    @patch('requests.put')
    def test_update(self, mock_put, mock_get, minds_client):
        response_mock(mock_get, self.mind_json)
        mind = minds_client.minds.get('mind_name')

        update_params = dict(
            name='mind_name',  # current name (required for update)
            new_name='mind_name2',
            datasources=[{'name': 'ds_name'}],
            provider='ollama',
            model_name='llama',
            parameters={
                'prompt_template': 'be polite'
            }
        )
        
        # Mock the PUT response for update
        updated_mind_json = self.mind_json.copy()
        updated_mind_json.update({
            'name': 'mind_name2',
            'provider': 'ollama',
            'model_name': 'llama',
            'parameters': {'prompt_template': 'be polite'},
            'datasources': [{'name': 'ds_name'}]
        })
        response_mock(mock_put, updated_mind_json)
        
        updated_mind = minds_client.minds.update(**update_params)

        args, kwargs = mock_put.call_args
        assert args[0].endswith(f'/api/v1/minds/{update_params["name"]}')  # Use the name we passed to update

        # Remove current name from expected request
        expected_request = update_params.copy()
        del expected_request['name']  # name is in URL, not request body
        expected_request['name'] = update_params['new_name']  # new_name becomes name in request
        del expected_request['new_name']
        
        assert kwargs['json'] == expected_request

    @patch('requests.get')
    def test_get(self, mock_get, minds_client):
        response_mock(mock_get, self.mind_json)

        mind = minds_client.minds.get('my_mind')
        self._compare_mind(mind, self.mind_json)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/v1/minds/my_mind')

    @patch('requests.get')
    def test_list(self, mock_get, minds_client):
        response_mock(mock_get, [self.mind_json])
        minds_list = minds_client.minds.list()
        assert len(minds_list) == 1
        self._compare_mind(minds_list[0], self.mind_json)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/v1/minds')

    @patch('requests.delete')
    def test_delete(self, mock_del, minds_client):
        minds_client.minds.drop('my_name')

        args, _ = mock_del.call_args
        assert args[0].endswith('/api/v1/minds/my_name')

    @patch('requests.get')
    @patch('minds.minds.OpenAI')
    def test_completion(self, mock_openai, mock_get, minds_client):
        response_mock(mock_get, self.mind_json)
        mind = minds_client.minds.get('mind_name')

        def openai_completion_f(messages, *args, **kwargs):
            # echo question
            answer = messages[0]['content']

            response = Mock()
            choice = Mock()
            choice.message.content = answer
            choice.delta.content = answer  # for stream
            response.choices = [choice]

            if kwargs.get('stream'):
                return [response]
            else:
                return response

        mock_openai().chat.completions.create.side_effect = openai_completion_f

        question = 'the ultimate question'

        answer = mind.completion(question)
        assert answer == question

        success = False
        for chunk in mind.completion(question, stream=True):
            if question == chunk.lower():
                success = True
        assert success is True
