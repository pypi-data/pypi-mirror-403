import asyncio
import time

import httpx

from wtwco_igloo.extensions.utils.retry_settings import RetrySettings
from wtwco_igloo.logger import logger


class RetryHttpxClient:
    def __init__(
        self,
        httpx_client: httpx.Client,
        retry_settings: RetrySettings,
    ):
        self._httpx_client = httpx_client
        self._initial_delay = retry_settings.initial_delay
        self._maximum_wait_time = retry_settings.maximum_wait_time
        self._status_codes = retry_settings.status_codes
        self._backoff_multiplier = retry_settings.backoff_multiplier

    def request(self, *args, **kwargs) -> httpx.Response:
        response = self._httpx_client.request(*args, **kwargs)

        delay = min(self._initial_delay, self._maximum_wait_time)
        total_wait_time = 0.0
        attempts = 1
        while response.status_code in self._status_codes and delay > 0:
            method = kwargs.get("method", args[0] if args else "REQUEST")
            url = kwargs.get("url", args[1] if len(args) > 1 else "unknown")
            logger.info(
                f"{method} {url} returned {response.status_code} with text {response.text}, retrying in {delay}s... (attempt {attempts}"
            )
            time.sleep(delay)
            total_wait_time += delay
            delay = min(delay * self._backoff_multiplier, self._maximum_wait_time - total_wait_time)
            response = self._httpx_client.request(*args, **kwargs)
            attempts += 1

        return response

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped client"""
        return getattr(self._httpx_client, name)


class RetryAsyncHttpxClient:
    def __init__(
        self,
        httpx_async_client: httpx.AsyncClient,
        retry_settings: RetrySettings,
    ):
        self._httpx_async_client = httpx_async_client
        self._initial_delay = retry_settings.initial_delay
        self._maximum_wait_time = retry_settings.maximum_wait_time
        self._status_codes = retry_settings.status_codes
        self._backoff_multiplier = retry_settings.backoff_multiplier

    async def request(self, *args, **kwargs) -> httpx.Response:
        response = await self._httpx_async_client.request(*args, **kwargs)

        delay = min(self._initial_delay, self._maximum_wait_time)
        total_wait_time = 0.0
        attempts = 1
        while response.status_code in self._status_codes and delay > 0:
            method = kwargs.get("method", args[0] if args else "REQUEST")
            url = kwargs.get("url", args[1] if len(args) > 1 else "unknown")
            logger.info(
                f"{method} {url} returned {response.status_code} with text {response.text}, retrying in {delay}s... (attempt {attempts}"
            )
            await asyncio.sleep(delay)
            total_wait_time += delay
            delay = min(delay * self._backoff_multiplier, self._maximum_wait_time - total_wait_time)
            response = await self._httpx_async_client.request(*args, **kwargs)
            attempts += 1

        return response

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped async client"""
        return getattr(self._httpx_async_client, name)
