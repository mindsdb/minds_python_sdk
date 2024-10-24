
from unittest.mock import Mock
from unittest.mock import patch


from minds.datasources.examples import example_ds

def get_client():
    from minds.client import Client
    return Client(API_KEY)

from minds import rest_api

# patch _raise_for_status
rest_api._raise_for_status = Mock()
#
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
        def check_ds_created(ds, mock_post):
            self._compare_ds(ds, example_ds)
            args, kwargs = mock_post.call_args

            assert kwargs['headers'] == {'Authorization': 'Bearer ' + API_KEY}
            assert kwargs['json'] == example_ds.model_dump()
            assert args[0] == 'https://mdb.ai/api/datasources'

        check_ds_created(ds, mock_post)

        # with replace
        ds = client.datasources.create(example_ds, replace=True)
        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/datasources/{example_ds.name}')

        check_ds_created(ds, mock_post)

        # with update
        ds = client.datasources.create(example_ds, update=True)
        check_ds_created(ds, mock_put)

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
        assert args[0].endswith(f'/api/datasources/ds_name')

    @patch('requests.get')
    def test_list_datasources(self, mock_get):
        client = get_client()

        response_mock(mock_get, [example_ds.model_dump()])
        ds_list = client.datasources.list()
        assert len(ds_list) == 1
        ds = ds_list[0]
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/datasources')


class TestMinds:

    mind_json = {
        'model_name': 'gpt-4o',
        'name': 'test_mind',
        'datasources': ['example_ds'],
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
        provider = 'openai'

        response_mock(mock_get, self.mind_json)
        create_params = {
            'name': mind_name,
            'prompt_template': prompt_template,
            'datasources': datasources
        }
        mind = client.minds.create(**create_params)

        def check_mind_created(mind, mock_post, create_params):
            args, kwargs = mock_post.call_args
            assert args[0].endswith('/api/projects/mindsdb/minds')
            request = kwargs['json']
            for key in ('name', 'datasources', 'provider', 'model_name'),:
                assert request.get(key) == create_params.get(key)
            assert create_params.get('prompt_template') == request.get('parameters', {}).get('prompt_template')

            self.compare_mind(mind, self.mind_json)

        check_mind_created(mind, mock_post, create_params)

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

        check_mind_created(mind, mock_post, create_params)

        # -- with update --
        mock_del.reset_mock()
        mind = client.minds.create(update=True, **create_params)
        # is not deleted
        assert not mock_del.called

        check_mind_created(mind, mock_put, create_params)

    @patch('requests.get')
    @patch('requests.patch')
    def test_update(self, mock_patch, mock_get):
        client = get_client()

        response_mock(mock_get, self.mind_json)
        mind = client.minds.get('mind_name')

        update_params = dict(
            name='mind_name2',
            datasources=['ds_name'],
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
        assert args[0].endswith(f'/api/projects/mindsdb/minds/my_mind')

    @patch('requests.get')
    def test_list(self, mock_get):
        client = get_client()

        response_mock(mock_get, [self.mind_json])
        minds_list = client.minds.list()
        assert len(minds_list) == 1
        self.compare_mind(minds_list[0], self.mind_json)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/projects/mindsdb/minds')

    @patch('requests.delete')
    def test_delete(self, mock_del):
        client = get_client()
        client.minds.drop('my_name')

        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/projects/mindsdb/minds/my_name')

    @patch('requests.get')
    @patch('minds.minds.OpenAI')
    def test_completion(self, mock_openai, mock_get):
        client = get_client()

        response_mock(mock_get, self.mind_json)
        mind = client.minds.get('mind_name')

        openai_response = 'how can I assist you today?'

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

