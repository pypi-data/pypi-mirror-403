from wtwco_igloo.api_client import AuthenticatedClient
from wtwco_igloo.extensions.utils.authentication.retry_httpx_client import RetryAsyncHttpxClient, RetryHttpxClient
from wtwco_igloo.extensions.utils.retry_settings import RetrySettings


class AuthenticatedClientWithRetries:
    def __init__(
        self,
        auth_client: AuthenticatedClient,
        retry_settings: RetrySettings,
    ):
        self._auth_client = auth_client
        self._retry_settings = retry_settings

    def get_httpx_client(self, *args, **kwargs):
        return RetryHttpxClient(
            self._auth_client.get_httpx_client(*args, **kwargs),
            self._retry_settings,
        )

    def get_async_httpx_client(self, *args, **kwargs):
        return RetryAsyncHttpxClient(
            self._auth_client.get_async_httpx_client(*args, **kwargs),
            self._retry_settings,
        )

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped client"""
        return getattr(self._auth_client, name)
