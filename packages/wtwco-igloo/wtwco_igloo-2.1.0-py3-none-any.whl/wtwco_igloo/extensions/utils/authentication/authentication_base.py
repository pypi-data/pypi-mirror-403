import locale
import platform
from importlib import metadata
from typing import Any, Union, cast
from urllib.parse import urljoin

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from msal import (
    ConfidentialClientApplication,
    PublicClientApplication,
    SerializableTokenCache,
)

from wtwco_igloo.api_client import AuthenticatedClient
from wtwco_igloo.extensions.utils.authentication.authenticated_client_with_retries import AuthenticatedClientWithRetries
from wtwco_igloo.extensions.utils.authentication.custom_http_client import (
    custom_http_client,
)
from wtwco_igloo.extensions.utils.authentication.token_cache import _TokenCacheManager
from wtwco_igloo.extensions.utils.errors.connection_errors import AuthenticationError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import (
    _log_and_get_exception,
)
from wtwco_igloo.extensions.utils.helpers import _standardise_url
from wtwco_igloo.extensions.utils.retry_settings import RetrySettings


class _AuthenticationManagerBase:
    def __init__(
        self,
        api_url: str,
        client_id: str,
        tenant_id: str,
        enable_broker_on_windows: bool,
        retry_settings: RetrySettings,
    ):
        self._api_url = api_url
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._microsoft_login_url = "https://login.microsoftonline.com/"
        self._app: Union[PublicClientApplication, ConfidentialClientApplication, None] = None
        self._enable_broker_on_windows = enable_broker_on_windows
        self._retry_settings = retry_settings
        self._scope: Union[str, None] = None
        self._token: Union[str, None] = None
        self._auth_client_with_retries: Union[AuthenticatedClientWithRetries, None] = None
        self._auth_client_refresh_requested: bool = False
        self._headers: dict[str, str] = {"User-Agent": self._get_default_user_agent()}

    def _from_certificate(self, thumbprint: str, certificate_path: str) -> None:
        self._scope = _standardise_url(self._api_url, ".default")
        with open(certificate_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=default_backend())

        self._app = self._get_confidential_client_application(
            client_id=self._client_id,
            authority=urljoin(self._microsoft_login_url, self._tenant_id),
            client_credential={
                "thumbprint": thumbprint,
                "private_key": private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ).decode("utf-8"),
            },
        )
        result = self._app.acquire_token_for_client(scopes=[self._scope])

        if result.get("error_description") is not None:
            raise _log_and_get_exception(
                AuthenticationError,
                "Failed to authenticate from certificate.",
                result.get("error"),
            )
        else:
            self._token = result["access_token"]

    def _from_device_code(self, **kwargs: bool) -> None:
        token_cache_manager = _TokenCacheManager(self._client_id, **kwargs)
        self._scope = _standardise_url(self._api_url, "user_impersonation")
        self._app = self._get_public_client_application(
            client_id=self._client_id,
            authority=urljoin(self._microsoft_login_url, self._tenant_id),
            token_cache=token_cache_manager._get_token_cache(),
        )

        attempt_login = self._try_login_with_existing_account()
        result = attempt_login if attempt_login else self._perform_device_code_flow()

        if "access_token" in result:
            self._token = result["access_token"]
            token_cache_manager._serialise_token()
        else:
            raise _log_and_get_exception(
                AuthenticationError,
                "Failed to authenticate from device code.",
                result.get("error"),
            )

    def _from_interactive_token(self, **kwargs: bool) -> None:
        # For information on using the Windows Account Manager broker see:
        # https://learn.microsoft.com/en-us/entra/msal/python/advanced/wam

        token_cache_manager = _TokenCacheManager(self._client_id, **kwargs)
        self._scope = _standardise_url(self._api_url, "user_impersonation")

        self._app = self._get_public_client_application(
            client_id=self._client_id,
            authority=urljoin(self._microsoft_login_url, self._tenant_id),
            token_cache=token_cache_manager._get_token_cache(),
        )

        attempt_login = self._try_login_with_existing_account()
        result = (
            attempt_login
            if attempt_login
            else self._app.acquire_token_interactive(
                scopes=[self._scope],
                parent_window_handle=self._app.CONSOLE_WINDOW_HANDLE,
            )
        )

        if "access_token" in result:
            self._token = result["access_token"]
            token_cache_manager._serialise_token()

        else:
            raise _log_and_get_exception(
                AuthenticationError,
                "Failed to authenticate from interactive token.",
                result.get("error"),
            )

    def _from_secret(self, secret: str) -> None:
        self._scope = _standardise_url(self._api_url, ".default")
        self._app = self._get_confidential_client_application(
            client_id=self._client_id,
            authority=urljoin(self._microsoft_login_url, self._tenant_id),
            client_credential=secret,
        )
        result = self._app.acquire_token_for_client(scopes=[self._scope])

        if result.get("error_description") is not None:
            raise _log_and_get_exception(
                AuthenticationError,
                "Failed to get the authentication token from device code.",
                result.get("error"),
            )
        else:
            self._token = result["access_token"]

    def _get_authenticated_client(self) -> AuthenticatedClient:
        if self._auth_client_with_retries and not self._auth_client_refresh_requested:
            return cast(AuthenticatedClient, self._auth_client_with_retries)
        elif self._token:
            self._auth_client_refresh_requested = False
            auth_client = AuthenticatedClient(
                self._api_url,
                token=self._token,
                verify_ssl=True,
                headers=self._headers,
            )
            self._auth_client_with_retries = AuthenticatedClientWithRetries(
                auth_client,
                retry_settings=self._retry_settings,
            )
            return cast(AuthenticatedClient, self._auth_client_with_retries)
        raise _log_and_get_exception(
            AuthenticationError,
            "No token found. Please authenticate first.",
        )

    def _recreate_client_with_new_headers(self) -> None:
        """Recreates self._auth_client_with_retries with the headers in self._headers.

        This method avoids creating a new httpx.Client, which is an expensive operation due to SSL handshakes and so on.
        """
        if not self._auth_client_with_retries:
            return
        if not self._token:
            raise _log_and_get_exception(
                AuthenticationError,
                "No token found. Please authenticate first.",
            )

        httpx_client = self._auth_client_with_retries._auth_client.get_httpx_client()
        async_httpx_client = self._auth_client_with_retries._auth_client.get_async_httpx_client()

        httpx_client.headers = self._headers
        async_httpx_client.headers = self._headers

        auth_client = AuthenticatedClient(
            self._api_url,
            token=self._token,
            verify_ssl=True,
            headers=self._headers,
        )

        auth_client.set_httpx_client(httpx_client)
        auth_client.set_async_httpx_client(async_httpx_client)

        self._auth_client_with_retries = AuthenticatedClientWithRetries(
            auth_client,
            retry_settings=self._retry_settings,
        )

    def _update_headers(self, headers: dict[str, str]) -> None:
        self._headers.update(headers)
        self._recreate_client_with_new_headers()

    def _remove_headers(self, *headers: str) -> None:
        for key in headers:
            self._headers.pop(key, None)
        self._recreate_client_with_new_headers()

    def _try_login_with_existing_account(self) -> Union[dict[str, Any], None]:
        if self._app is None:
            raise _log_and_get_exception(
                AuthenticationError,
                "The application instance is not set.",
            )
        accounts = self._app.get_accounts()
        result = None
        if accounts and len(accounts) > 0:
            account = accounts[0]
            print(f"Logging in as account {account['username']}")
            result = self._app.acquire_token_silent(scopes=[self._scope], account=account)

        return result

    def _get_confidential_client_application(
        self,
        client_id: str,
        authority: str,
        client_credential: Union[str, dict[str, str]],
    ) -> ConfidentialClientApplication:
        return ConfidentialClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_credential,
            http_client=self._get_authenticating_client(),
        )

    def _get_authenticating_client(self) -> requests.Session:
        http_client = custom_http_client()
        http_client.headers.update({"User-Agent": self._get_default_user_agent()})
        return http_client

    def _get_default_user_agent(self) -> str:
        os_info = platform.system() + " " + platform.release()
        os_version = platform.version()
        locale_info = self._get_formatted_locale()
        python_version = platform.python_version()
        sdk_version = metadata.version("wtwco_igloo")
        return f"Mozilla/5.0 ({os_info}; {os_version}; \
            {locale_info}) Python/{python_version} Igloo Python SDK/{sdk_version}"

    def _get_public_client_application(
        self,
        client_id: str,
        authority: str,
        token_cache: SerializableTokenCache,
    ) -> PublicClientApplication:
        return PublicClientApplication(
            client_id=client_id,
            authority=authority,
            token_cache=token_cache,
            enable_broker_on_windows=self._enable_broker_on_windows,
            http_client=self._get_authenticating_client(),
        )

    def _perform_device_code_flow(self) -> dict[str, Any]:
        if isinstance(self._app, PublicClientApplication):
            flow: dict[str, Any] = self._app.initiate_device_flow(scopes=[self._scope])
            if "user_code" not in flow:
                raise _log_and_get_exception(AuthenticationError, "Failed to create device flow.", flow)
            # Print out the device code message to the user so they know what to do next
            print(flow["message"])
            # This call will block until the user has completed entering the code and successfully authenticated
            result: dict[str, Any] = self._app.acquire_token_by_device_flow(flow)
            return result
        else:
            raise _log_and_get_exception(
                AuthenticationError,
                "Device code flow is only available for public client applications.",
            )

    @staticmethod
    def _get_formatted_locale() -> Union[str, None]:
        locale.setlocale(locale.LC_ALL, "")
        return locale.getlocale()[0]
