from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError
from wtwco_igloo.logger import logger


class ConnectionError(WtwcoIglooError):
    """Base class for connection errors."""

    def __init__(self, *args):
        super().__init__(*args)


class AuthenticationError(ConnectionError):
    """Exception raised for token retrieval failures."""

    def __init__(self, message, error_info):
        super().__init__(message, error_info)

    def _log_error(self):
        logger.error(self.message)

    @property
    def message(self):
        return self.args[0]

    @property
    def error_info(self):
        return self.args[1]


class UnsuccessfulRequestError(ConnectionError):
    """Exception raised when a request does not return a successful http status code."""

    def __init__(self, message: str, status_code, response):
        self.message = message
        super().__init__(status_code, response)

    @property
    def status_code(self):
        return self.args[0]

    @property
    def response(self):
        return self.args[1]

    def __str__(self) -> str:
        return self.message
