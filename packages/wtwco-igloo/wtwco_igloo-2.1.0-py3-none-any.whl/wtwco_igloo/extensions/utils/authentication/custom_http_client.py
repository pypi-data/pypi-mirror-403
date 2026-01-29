import functools

import requests  # Lazy load


def custom_http_client() -> requests.Session:
    http_client = requests.Session()
    http_client.verify = True
    # Requests, does not support session - wide timeout
    # But you can patch that (https://github.com/psf/requests/issues/3341):
    http_client.request = functools.partial(http_client.request, timeout=None)  # type: ignore
    # Enable a minimal retry. Better than nothing.
    # https://github.com/psf/requests/blob/v2.25.1/requests/adapters.py#L94-L108
    a = requests.adapters.HTTPAdapter(max_retries=1)
    http_client.mount("http://", a)
    http_client.mount("https://", a)
    return http_client
