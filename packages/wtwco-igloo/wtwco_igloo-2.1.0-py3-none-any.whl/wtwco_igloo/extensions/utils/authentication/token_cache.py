import os

from msal import SerializableTokenCache

from wtwco_igloo.extensions.utils.errors.connection_errors import AuthenticationError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception


class _TokenCacheManager:
    def __init__(self, client_id: str, **kwargs: bool):
        self._client_id = client_id
        self._no_cache = kwargs.get("no_cache", False)
        self._token_cache_path = self._get_token_cache_path(client_id)
        self._token_cache = SerializableTokenCache()

    def _get_token_cache(self) -> SerializableTokenCache:
        if not self._no_cache and self._token_cache_path_exists():
            with open(self._token_cache_path, "r") as f:
                self._token_cache.deserialize(f.read())
        return self._token_cache

    def _serialise_token(self) -> None:
        if self._token_cache.has_state_changed:
            os.makedirs(os.path.dirname(self._token_cache_path), exist_ok=True)
            with open(self._token_cache_path, "w") as f:
                f.write(self._token_cache.serialize())

    def _token_cache_path_exists(self) -> bool:
        return os.path.exists(self._token_cache_path)

    def _clear_token_cache(self) -> None:
        if self._token_cache_path_exists():
            os.remove(self._token_cache_path)

    @staticmethod
    def _get_token_cache_path(client_id: str) -> str:
        local_env = os.getenv("LOCALAPPDATA")
        if local_env is not None:
            return os.path.join(local_env, "WTW", "wtwco_igloo", "cache", f"{client_id}.bin")

        raise _log_and_get_exception(
            AuthenticationError, "LOCALAPPDATA environment variable not found. Please set it to continue."
        )
