import os
import unittest
from unittest import mock


class FakeUnixSocketRpc:
    def __init__(self, *, socket_path, token, instance, timeout=30.0):
        self.socket_path = socket_path
        self.token = token
        self.instance = instance
        self.timeout = timeout
        self._authed = False

    def connect(self):
        return None

    def close(self):
        return None

    def add_event_handler(self, _handler):
        return None

    def request(self, method, params=None, *, timeout=None):
        if method == 'auth':
            self._authed = True
            return {'status': 'ok'}
        if method == 'whoami':
            return {
                'user': {'id': 1, 'email': 'script@simo.io'},
                'selected_instance': {'uid': 'inst-uid', 'slug': 'inst-slug'},
                'mqtt': {},
            }
        if method in (
            'list_zones',
            'list_categories',
            'list_components',
            'list_instance_users',
            'list_users',
        ):
            return []
        if method == 'get_settings':
            return {'timezone': 'UTC', 'location': '0,0'}
        raise RuntimeError(f'Unexpected method: {method}')


class EnvDefaultsTests(unittest.TestCase):
    def test_simo_client_uses_env_defaults_in_socket_mode(self):
        with mock.patch.dict(
            os.environ,
            {
                'SIMO_SDK_SOCKET_PATH': '/run/simo/simo-sdk-supervisor.sock',
                'SIMO_SDK_TOKEN': 'tok',
                'SIMO_SDK_INSTANCE': 'inst-slug',
            },
            clear=False,
        ):
            with mock.patch('simo_sdk.client.UnixSocketRpcClient', FakeUnixSocketRpc):
                from simo_sdk import SIMOClient

                home = SIMOClient()
                self.assertEqual(home._instance_slug, 'inst-slug')
                self.assertEqual(home._instance_uid, 'inst-uid')


if __name__ == '__main__':
    unittest.main()

