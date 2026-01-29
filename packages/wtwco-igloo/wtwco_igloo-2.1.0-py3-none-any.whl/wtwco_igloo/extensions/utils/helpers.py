import os
import time
from typing import TYPE_CHECKING, Any, Generator
from urllib.parse import urlsplit, urlunsplit

from wtwco_igloo.api_client.models import (
    RunState,
)
from wtwco_igloo.extensions.utils.errors.run_errors import RunStateTimeOutError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import (
    FilePathNotFoundError,
    NonCsvFileError,
    _log_and_get_exception,
)

if TYPE_CHECKING:
    from wtwco_igloo import Run
    from wtwco_igloo.extensions.utils.types.run_types import OperatorFunction, SensitivityOperatorFunction


def _create_adjustment_function(sensitivity_function: "SensitivityOperatorFunction", factor: Any) -> "OperatorFunction":
    return lambda x: sensitivity_function(x, factor)


def _validate_files_exist(files: list[str]) -> bool:
    non_existent_files = [file for file in files if not os.path.exists(file)]
    if len(non_existent_files) > 0:
        raise _log_and_get_exception(
            FilePathNotFoundError,
            (
                "Please ensure file paths are correct. The following files do not exist:"
                f"{', '.join(non_existent_files)}."
            ),
        )
    return True


def _validate_files_are_csv(files: list[str]) -> bool:
    non_csv_files = [file for file in files if not str(file).endswith(".csv")]
    if len(non_csv_files) > 0:
        raise _log_and_get_exception(
            NonCsvFileError,
            f"Only csv files are accepted. The following files are not csv: {', '.join(non_csv_files)}.",
        )
    return True


def _ensure_runs_are_processed(runs: list["Run"], run_processing_minutes: int) -> None:
    for wait_seconds in _wait_iterations(run_processing_minutes):
        if all(run.check_status() != RunState.PROCESSING for run in runs):
            return
        time.sleep(wait_seconds)

    raise _log_and_get_exception(
        RunStateTimeOutError,
        f"Runs are still processing after reaching the total wait time limit of {run_processing_minutes} minutes.\
        Please check the status of the runs.",
    )


def _wait_iterations(run_processing_minutes: int) -> Generator[float, None, None]:
    NUMBER_OF_ATTEMPTS = 15  # noqa: N806
    SCALING_FACTOR = 2  # noqa: N806
    wait_time = (run_processing_minutes * 60) / sum(SCALING_FACTOR**i for i in range(NUMBER_OF_ATTEMPTS))
    for i in range(NUMBER_OF_ATTEMPTS):
        yield wait_time * (SCALING_FACTOR**i)


def _standardise_url(url: str, path: str) -> str:
    parsed_url = urlsplit(url)
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, path, "", ""))


def _casefold_equals(a: str, b: str) -> bool:
    """Return True if two strings are equal, ignoring case (using casefold)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a.casefold() == b.casefold()
