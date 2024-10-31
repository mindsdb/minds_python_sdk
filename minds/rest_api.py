import requests

import minds.exceptions as exc


def _raise_for_status(response):
    if response.status_code == 404:
        raise exc.ObjectNotFound(response.text)

    if response.status_code == 403:
        raise exc.Forbidden(response.text)

    if response.status_code == 401:
        raise exc.Unauthorized(response.text)

    if 400 <= response.status_code < 600:
        raise exc.UnknownError(f'{response.reason}: {response.text}')


class RestAPI:
    def __init__(self, api_key, base_url=None):
        if base_url is None:
            base_url = 'https://mdb.ai'

        base_url = base_url.rstrip('/')
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

    def delete(self, url, data=None):
        resp = requests.delete(
            self.base_url + url,
            headers=self._headers(),
            json=data
        )

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

    def put(self, url, data):
        resp = requests.put(
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
