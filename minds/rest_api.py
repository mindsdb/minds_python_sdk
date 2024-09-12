import requests


def _raise_for_status(response):
    # show response text in error
    if 400 <= response.status_code < 600:
        raise requests.HTTPError(f'{response.reason}: {response.text}', response=response)


class RestAPI:
    def __init__(self, api_key, base_url=None):
        if base_url is None:
            base_url = 'https://mdb.ai/'

        base_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url = base_url + '/api'
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self):
        return {'Authorization': 'Bearer ' + self.api_key}

    def get(self, url):
        resp = requests.get(self.base_url + url, headers=self._headers())

        _raise_for_status(resp)
        return resp

    def delete(self, url):
        resp = requests.delete(self.base_url + url, headers=self._headers())

        _raise_for_status(resp)
        return resp

    def post(self, url, data):
        resp = requests.post(
            self.base_url + url,
            headers=self._headers(),
            json=data,
        )

        _raise_for_status(resp)
        return resp

    def patch(self, url, data):
        resp = requests.patch(
            self.base_url + url,
            headers=self._headers(),
            json=data,
        )

        _raise_for_status(resp)
        return resp
