from typing import Any, Type

from wtwco_igloo.logger import logger


def _log_and_get_exception(exception_class: Type["WtwcoIglooError"], message: str, *args: Any) -> "WtwcoIglooError":
    """Logs the error using the exception's _log_error method and returns the exception instance."""
    exception = exception_class(message, *args)
    exception._log_error()
    return exception


class WtwcoIglooError(Exception):
    """Base class for all exceptions raised by the wtwco-igloo package."""

    def __init__(self, *args):
        super().__init__(*args)

    def _log_error(self):
        logger.error(", ".join(map(str, self.args)), exc_info=1)


class FolderNotFoundError(WtwcoIglooError, FileNotFoundError):
    "Exception raised when a folder is not found."

    def __init__(self, *args):
        super().__init__(*args)


class FilePathNotFoundError(WtwcoIglooError, FileNotFoundError):
    "Exception raised when a file is not found."

    def __init__(self, *args):
        super().__init__(*args)


class InvalidFileError(WtwcoIglooError, ValueError):
    "Exception raised when a file is invalid."

    def __init__(self, *args):
        super().__init__(*args)


class NonCsvFileError(InvalidFileError):
    "Exception raised when a file is not a CSV file."

    def __init__(self, *args):
        super().__init__(*args)


class UnexpectedResponseError(WtwcoIglooError):
    "Exception raised when an unexpected response is received."

    def __init__(self, *args):
        super().__init__(*args)
