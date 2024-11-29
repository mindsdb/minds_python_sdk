
from unittest.mock import Mock
from unittest.mock import patch


from minds.datasources.examples import example_ds
from minds.knowledge_bases import EmbeddingConfig, KnowledgeBaseConfig, VectorStoreConfig


def get_client():
    from minds.client import Client
    return Client(API_KEY)


from minds import rest_api

# patch _raise_for_status
rest_api._raise_for_status = Mock()


def response_mock(mock, data):
    def side_effect(*args, **kwargs):
        r_mock = Mock()
        r_mock.status_code = 200
        r_mock.json.return_value = data
        return r_mock
    mock.side_effect = side_effect


API_KEY = '1234567890abc'


class TestDatasources:

    def _compare_ds(self, ds1, ds2):
        assert ds1.name == ds2.name
        assert ds1.engine == ds2.engine
        assert ds1.description == ds2.description
        assert ds1.connection_data == ds2.connection_data
        assert ds1.tables == ds2.tables

    @patch('requests.get')
    @patch('requests.put')
    @patch('requests.post')
    @patch('requests.delete')
    def test_create_datasources(self, mock_del, mock_post, mock_put, mock_get):
        client = get_client()
        response_mock(mock_get, example_ds.model_dump())

        ds = client.datasources.create(example_ds)

        def check_ds_created(ds, mock_post, url):
            self._compare_ds(ds, example_ds)
            args, kwargs = mock_post.call_args

            assert kwargs['headers'] == {'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'}
            assert kwargs['json'] == example_ds.model_dump()
            assert args[0] == url

        check_ds_created(ds, mock_post, 'https://mdb.ai/api/datasources')

        # with update
        ds = client.datasources.create(example_ds, update=True)
        check_ds_created(ds, mock_put, f'https://mdb.ai/api/datasources/{ds.name}')

    @patch('requests.get')
    def test_get_datasource(self, mock_get):
        client = get_client()

        response_mock(mock_get, example_ds.model_dump())
        ds = client.datasources.get(example_ds.name)
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/datasources/{example_ds.name}')

    @patch('requests.delete')
    def test_delete_datasource(self, mock_del):
        client = get_client()

        client.datasources.drop('ds_name')

        args, _ = mock_del.call_args
        assert args[0].endswith('/api/datasources/ds_name')

    @patch('requests.get')
    def test_list_datasources(self, mock_get):
        client = get_client()

        response_mock(mock_get, [example_ds.model_dump()])
        ds_list = client.datasources.list()
        assert len(ds_list) == 1
        ds = ds_list[0]
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/datasources')


class TestKnowledgeBases:

    def _compare_knowledge_base(self, knowledge_base, config):
        assert knowledge_base.name == config.name

    @patch('requests.get')
    @patch('requests.post')
    def test_create_knowledge_bases(self, mock_post, mock_get):
        client = get_client()

        test_embedding_config = EmbeddingConfig(
            provider='openai',
            model='gpt-4o',
            params={
                'k1': 'v1'
            }
        )
        test_vector_store_connection_data = {
            'user': 'test_user',
            'password': 'test_password',
            'host': 'boop.mindsdb.com',
            'port': '5432',
            'database': 'test',
        }
        test_vector_store_config = VectorStoreConfig(
            engine='pgvector',
            connection_data=test_vector_store_connection_data,
            table='test_table'
        )
        test_knowledge_base_config = KnowledgeBaseConfig(
            name='test_kb',
            description='Test knowledge base',
            vector_store_config=test_vector_store_config,
            embedding_config=test_embedding_config,
            params={
                'k1': 'v1'
            }
        )
        response_mock(mock_get, test_knowledge_base_config.model_dump())

        created_knowledge_base = client.knowledge_bases.create(test_knowledge_base_config)
        self._compare_knowledge_base(created_knowledge_base, test_knowledge_base_config)

        args, kwargs = mock_post.call_args

        assert kwargs['headers'] == {'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'}

        expected_create_request = {
            'name': test_knowledge_base_config.name,
            'description': test_knowledge_base_config.description,
            'vector_store': {
                'engine': test_vector_store_config.engine,
                'connection_data': test_vector_store_config.connection_data,
                'table': test_vector_store_config.table
            },
            'embedding_model': {
                'provider': test_embedding_config.provider,
                'name': test_embedding_config.model,
                'k1': 'v1'
            },
            'params': {
                'k1': 'v1'
            }
        }

        assert kwargs['json'] == expected_create_request
        assert args[0] == 'https://mdb.ai/api/knowledge_bases'

    @patch('requests.get')
    def test_get_knowledge_base(self, mock_get):
        client = get_client()

        test_embedding_config = EmbeddingConfig(
            provider='openai',
            model='gpt-4o',
            params={
                'k1': 'v1'
            }
        )
        test_vector_store_connection_data = {
            "user": "test_user",
            "password": "test_password",
            "host": "boop.mindsdb.com",
            "port": "5432",
            "database": "test",
        }
        test_vector_store_config = VectorStoreConfig(
            engine='pgvector',
            connection_data=test_vector_store_connection_data,
            table='test_table'
        )
        test_knowledge_base_config = KnowledgeBaseConfig(
            name='test_kb',
            description='Test knowledge base',
            vector_store_config=test_vector_store_config,
            embedding_config=test_embedding_config
        )

        # Expected response from MindsDB API server.
        get_response = {
            'created_at': '2024-11-15',
            'embedding_model': 'test_kb_embeddings',
            'id': 1,
            'name': 'test_kb',
            'params': {},
            'project_id': 1,
            'updated_at': '2024-11-15',
            'vector_database': 'test_kb_vector_store',
            'vector_database_table': 'test_table'
        }
        response_mock(mock_get, get_response)
        get_knowledge_base = client.knowledge_bases.get(test_knowledge_base_config.name)
        self._compare_knowledge_base(get_knowledge_base, test_knowledge_base_config)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/knowledge_bases/{test_knowledge_base_config.name}')

    @patch('requests.delete')
    def test_delete_knowledge_base(self, mock_del):
        client = get_client()

        client.knowledge_bases.drop('test_kb')

        args, _ = mock_del.call_args
        assert args[0].endswith('/api/knowledge_bases/test_kb')

    @patch('requests.get')
    def test_list_knowledge_bases(self, mock_get):
        client = get_client()

        test_embedding_config = EmbeddingConfig(
            provider='openai',
            model='gpt-4o',
            params={
                'k1': 'v1'
            }
        )
        test_vector_store_connection_data = {
            "user": "test_user",
            "password": "test_password",
            "host": "boop.mindsdb.com",
            "port": "5432",
            "database": "test",
        }
        test_vector_store_config = VectorStoreConfig(
            engine='pgvector',
            connection_data=test_vector_store_connection_data,
            table='test_table'
        )
        test_knowledge_base_config = KnowledgeBaseConfig(
            name='test_kb',
            description='Test knowledge base',
            vector_store_config=test_vector_store_config,
            embedding_config=test_embedding_config
        )

        # Expected response from MindsDB API server.
        get_response = {
            'created_at': '2024-11-15',
            'embedding_model': 'test_kb_embeddings',
            'id': 1,
            'name': 'test_kb',
            'params': {},
            'project_id': 1,
            'updated_at': '2024-11-15',
            'vector_database': 'test_kb_vector_store',
            'vector_database_table': 'test_table'
        }
        response_mock(mock_get, [get_response])
        knowledge_base_list = client.knowledge_bases.list()
        assert len(knowledge_base_list) == 1
        knowledge_base = knowledge_base_list[0]
        self._compare_knowledge_base(knowledge_base, test_knowledge_base_config)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/knowledge_bases')


class TestMinds:

    mind_json = {
        'model_name': 'gpt-4o',
        'name': 'test_mind',
        'datasources': ['example_ds'],
        'knowledge_bases': ['example_kb'],
        'provider': 'openai',
        'parameters': {
            'prompt_template': "Answer the user's question"
        },
        'created_at': 'Thu, 26 Sep 2024 13:40:57 GMT',
        'updated_at': 'Thu, 26 Sep 2024 13:40:57 GMT',
    }

    def compare_mind(self, mind, mind_json):
        assert mind.name == mind_json['name']
        assert mind.model_name == mind_json['model_name']
        assert mind.provider == mind_json['provider']
        assert mind.parameters == mind_json['parameters']

    @patch('requests.get')
    @patch('requests.put')
    @patch('requests.post')
    @patch('requests.delete')
    def test_create(self, mock_del, mock_post, mock_put, mock_get):
        client = get_client()

        mind_name = 'test_mind'
        prompt_template = 'always agree'
        datasources = ['my_ds']
        knowledge_bases = ['example_kb']
        provider = 'openai'

        response_mock(mock_get, self.mind_json)
        create_params = {
            'name': mind_name,
            'prompt_template': prompt_template,
            'datasources': datasources,
            'knowledge_bases': knowledge_bases
        }
        mind = client.minds.create(**create_params)

        def check_mind_created(mind, mock_post, create_params, url):
            args, kwargs = mock_post.call_args
            assert args[0].endswith(url)
            request = kwargs['json']
            for key in ('name', 'datasources', 'knowledge_bases', 'provider', 'model_name'),:
                assert request.get(key) == create_params.get(key)
            assert create_params.get('prompt_template') == request.get('parameters', {}).get('prompt_template')

            self.compare_mind(mind, self.mind_json)

        check_mind_created(mind, mock_post, create_params, '/api/projects/mindsdb/minds')

        # -- with replace --
        create_params = {
            'name': mind_name,
            'prompt_template': prompt_template,
            'provider': provider,
        }
        mind = client.minds.create(replace=True, **create_params)

        # was deleted
        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/projects/mindsdb/minds/{mind_name}')

        check_mind_created(mind, mock_post, create_params, '/api/projects/mindsdb/minds')

        # -- with update --
        mock_del.reset_mock()
        mind = client.minds.create(update=True, **create_params)
        # is not deleted
        assert not mock_del.called

        check_mind_created(mind, mock_put, create_params, f'/api/projects/mindsdb/minds/{mind_name}')

    @patch('requests.get')
    @patch('requests.patch')
    def test_update(self, mock_patch, mock_get):
        client = get_client()

        response_mock(mock_get, self.mind_json)
        mind = client.minds.get('mind_name')

        update_params = dict(
            name='mind_name2',
            datasources=['ds_name'],
            knowledge_bases=['kb_name'],
            provider='ollama',
            model_name='llama',
            parameters={
                'prompt_template': 'be polite'
            }
        )
        mind.update(**update_params)

        args, kwargs = mock_patch.call_args
        assert args[0].endswith(f'/api/projects/mindsdb/minds/{self.mind_json["name"]}')

        assert kwargs['json'] == update_params

    @patch('requests.get')
    def test_get(self, mock_get):
        client = get_client()

        response_mock(mock_get, self.mind_json)

        mind = client.minds.get('my_mind')
        self.compare_mind(mind, self.mind_json)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/projects/mindsdb/minds/my_mind')

    @patch('requests.get')
    def test_list(self, mock_get):
        client = get_client()

        response_mock(mock_get, [self.mind_json])
        minds_list = client.minds.list()
        assert len(minds_list) == 1
        self.compare_mind(minds_list[0], self.mind_json)

        args, _ = mock_get.call_args
        assert args[0].endswith('/api/projects/mindsdb/minds')

    @patch('requests.delete')
    def test_delete(self, mock_del):
        client = get_client()
        client.minds.drop('my_name')

        args, _ = mock_del.call_args
        assert args[0].endswith('/api/projects/mindsdb/minds/my_name')

    @patch('requests.get')
    @patch('minds.minds.OpenAI')
    def test_completion(self, mock_openai, mock_get):
        client = get_client()

        response_mock(mock_get, self.mind_json)
        mind = client.minds.get('mind_name')

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
            if question == chunk.content.lower():
                success = True
        assert success is True
