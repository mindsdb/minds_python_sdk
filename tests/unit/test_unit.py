
from unittest.mock import Mock
from unittest.mock import patch


from minds.datasources.examples import example_ds

from minds.client import Client

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
    @patch('requests.post')
    @patch('requests.delete')
    def test_create_datasources(self, mock_del, mock_post, mock_get):
        # create

        client = Client(API_KEY)
        response_mock(mock_get, example_ds.model_dump())

        ds = client.datasources.create(example_ds)
        def check_ds_created(ds, mock_post):
            self._compare_ds(ds, example_ds)
            args, kwargs = mock_post.call_args

            assert kwargs['headers'] == {'Authorization': 'Bearer ' + API_KEY}
            assert kwargs['json'] == example_ds.model_dump()
            assert args[0] == 'https://mdb.ai//api/datasources'

        check_ds_created(ds, mock_post)

        # with replace
        ds = client.datasources.create(example_ds, replace=True)
        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/datasources/{example_ds.name}')

        check_ds_created(ds, mock_post)

    @patch('requests.get')
    def test_get_datasource(self, mock_get):
        client = Client(API_KEY)

        response_mock(mock_get, example_ds.model_dump())
        ds = client.datasources.get(example_ds.name)
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/datasources/{example_ds.name}')

    @patch('requests.delete')
    def test_delete_datasource(self, mock_del):
        client = Client(API_KEY)

        client.datasources.drop('ds_name')

        args, _ = mock_del.call_args
        assert args[0].endswith(f'/api/datasources/ds_name')

    @patch('requests.get')
    def test_list_datasources(self, mock_get):
        client = Client(API_KEY)

        response_mock(mock_get, [example_ds.model_dump()])
        ds_list = client.datasources.list()
        assert len(ds_list) == 1
        ds = ds_list[0]
        self._compare_ds(ds, example_ds)

        args, _ = mock_get.call_args
        assert args[0].endswith(f'/api/datasources')




