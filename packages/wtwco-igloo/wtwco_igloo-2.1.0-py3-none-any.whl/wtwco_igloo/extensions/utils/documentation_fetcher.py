from typing import Any
from urllib.parse import urlparse

from wtwco_igloo.extensions.connection import Connection
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator


class _DocumentationFetcher:
    def __init__(self, connection: Connection):
        self._connection = connection
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid

    def _get_kwargs(self, url: str) -> dict[str, Any]:
        return {
            "method": "get",
            "url": url,
        }

    def _is_safe_url(self, url: str) -> bool:
        """Validates that the URL is a relative path starting with /api/v"""
        parsed_url = urlparse(url)
        return url.startswith("/api/v") and not parsed_url.netloc and not parsed_url.scheme

    def _get_httpx_client(self):
        return self._connection._get_authenticated_client().get_httpx_client()

    def fetch_documentation(self, url: str) -> str:
        if not self._is_safe_url(url):
            raise ValueError(f"url must start with /api/v and have no network location or scheme, but was {url}")
        client = self._get_httpx_client()

        kwargs = self._get_kwargs(url)
        response = client.request(**kwargs)
        self._check_response_is_valid(response)
        text: str = response.text
        return text
