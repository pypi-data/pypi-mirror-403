import csv
import math
import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional, Union, cast
from urllib.parse import urljoin

from wtwco_igloo.api_client.api.data_groups import list_data_groups_for_run
from wtwco_igloo.api_client.api.data_table import get_data_table_for_run
from wtwco_igloo.api_client.api.input_data import get_input_data_for_table, update_input_data
from wtwco_igloo.api_client.api.jobs import create_job, get_job
from wtwco_igloo.api_client.api.o_data import get_o_data_for_run
from wtwco_igloo.api_client.api.output_data import get_output_data
from wtwco_igloo.api_client.api.result_table import get_result_table_for_run
from wtwco_igloo.api_client.api.result_tables import list_result_tables_for_run
from wtwco_igloo.api_client.api.run_results import list_run_results_for_run
from wtwco_igloo.api_client.api.runs import (
    delete_run_for_project,
    get_run,
    update_run_finalization_state,
    update_run_for_project,
)
from wtwco_igloo.api_client.models import (
    CreateJob,
    DataGroup,
    DataGroupArrayResponse,
    DataType,
    DeleteRunResult,
    DeleteRunResultResponse,
    GetODataForRunResponse200,
    GetODataForRunResponse200ValueItem,
    InputData,
    InputDataResponse,
    JobResponse,
    OutputData,
    OutputDataResponse,
    ResultTableNodeArrayResponse,
    RunError,
    RunFinalizationState,
    RunResponse,
    RunResultArrayResponse,
    RunState,
    TableData,
    TableDataResponse,
    UpdateInputData,
    UpdateRun,
)
from wtwco_igloo.api_client.models import Job as ClientJob
from wtwco_igloo.api_client.models import (
    ResultTableNode as ClientResultTableNode,
)
from wtwco_igloo.api_client.models import Run as ClientRun
from wtwco_igloo.api_client.models import (
    RunResult as ClientRunResult,
)
from wtwco_igloo.api_client.types import UNSET, Response, Unset
from wtwco_igloo.extensions.utils.callbacks.run_callbacks import (
    FileReferenceCopyPolicy,
    default_file_reference_copy_policy,
)
from wtwco_igloo.extensions.utils.errors.calculation_pool_errors import CalculationPoolNotFoundError
from wtwco_igloo.extensions.utils.errors.connection_errors import UnsuccessfulRequestError
from wtwco_igloo.extensions.utils.errors.run_errors import (
    DataTransformationError,
    OutputDataTableError,
    RunDeletionError,
    RunInputDictionaryKeyError,
    RunNamingError,
    RunParameterError,
)
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import (
    FolderNotFoundError,
    InvalidFileError,
    UnexpectedResponseError,
    _log_and_get_exception,
)
from wtwco_igloo.extensions.utils.helpers import (
    _casefold_equals,
    _create_adjustment_function,
    _ensure_runs_are_processed,
    _validate_files_are_csv,
    _validate_files_exist,
)
from wtwco_igloo.extensions.utils.validators.input_validator import _InputValidator
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator
from wtwco_igloo.extensions.utils.validators.run_input_validators import (
    RunAdjustmentDictValidator,
    SensitivityDictValidator,
)
from wtwco_igloo.logger import logger

if TYPE_CHECKING:
    from wtwco_igloo import Job, Project, RunResult, RunResultTableNode, UploadedFile
    from wtwco_igloo.extensions.utils.types.run_types import (
        OperatorFunction,
        RunAdjustmentDict,
        SensitivityDict,
        TableAdjustmentDict,
        TableSensitivityDict,
    )


class Run(object):
    """Represents a run in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the run.
        project (Project): The project for the run.
        workspace (Workspace): Workspace the project belongs to.
        name (str): Name of the run.
        parent_id (int): Optional. Identifier value of the run's parent.
        description (str): Description of the run.
        auto_delete_minutes (int): Optional. Life time of the run in minutes. If not set the run will not auto delete.
        cached_state (RunState): Returns the cached run state.
        cached_finalization_state (RunFinalizationState): What finalization state the run is in. One of Finalized,
            Finalizing, NotFinalized, or FinalizationRequested.
        errors (list[RunError]): List of errors that occured for this run.
        web_app_url (str): URL to the Igloo Cloud run.
        connection (Connection): Connection object used to authenticate with Igloo Cloud.
    """

    def __init__(self, project: "Project", run: dict[str, Any]) -> None:
        self.id: int = run["id"]
        self.project = project
        self.workspace = project.workspace
        self.name: str = run["name"]
        self.parent_id: Optional[int] = run["parentId"]
        self.description: str = run["description"]
        self.auto_delete_minutes: Optional[int] = run["autoDeletionTime"]
        self.cached_state: RunState = run["state"]
        self.cached_finalization_state: RunFinalizationState | None = run.get("finalizationState")
        self.errors: list[RunError] = run.get("errors", [])
        self.web_app_url: str = urljoin(project.web_app_url, f"runs/{self.id}/")
        self.connection = project.workspace.connection
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid
        self._validate_response = _ResponseValidator._validate_response
        self._validate_input = _InputValidator._validate
        self._import_classes()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Run):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.cached_state == other.cached_state
            and self.description == other.description
        )

    def __str__(self) -> str:
        return f"id: {self.id}, name: {self.name}, state: {self.cached_state}"

    def check_finalization_status(self) -> RunFinalizationState:
        """Retrieves the run's finalization status.

        Returns:
            Finalization status of the run. The following states are possible

            ``Finalized, Finalizing, NotFinalized, FinalizationRequested``

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_run.sync_detailed(
            workspace_id=self.workspace.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_run: ClientRun = self._validate_response(response, RunResponse, ClientRun)

        if isinstance(raw_run.finalization_state, Unset):
            raise _log_and_get_exception(UnexpectedResponseError, "Run finalization state is unknown.")
        else:
            self.cached_finalization_state = raw_run.finalization_state
            return self.cached_finalization_state

    def check_status(self) -> RunState:
        """Retrieves the run's status.

        Returns:
            Status of the run. The following states are possible

            ``COMPLETED, ERROR, INPROGRESS, PROCESSING, UNCALCULATED, WARNED``

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_run.sync_detailed(
            workspace_id=self.workspace.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_run: ClientRun = self._validate_response(response, RunResponse, ClientRun)

        if isinstance(raw_run.state, Unset):
            raise _log_and_get_exception(UnexpectedResponseError, "Run state is unknown.")
        else:
            self.cached_state = raw_run.state
            return self.cached_state

    def get_data_groups(self) -> list[dict[str, Any]]:
        """Returns a list of data groups used by the run.

        Returns:
            A list of data groups used by the run as dictionaries.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_data_groups_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_data_groups: list[DataGroup] = self._validate_response(response, DataGroupArrayResponse, DataGroup)

        return [data_group.to_dict() for data_group in raw_data_groups]

    def calculate(self, pool_name: str | None = None, pool_id: int | None = None) -> "Job":
        """Calculates the run.

        Args:
            pool_name: Name of the pool to use for calculating. If no pool name or id is given the default
                pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id: Id of the pool to use for calculating. Can be used instead of pool_name.

        Returns:
            Job representing the calculation job.

        Raises:
            CalculationPoolNotFoundError: The specified pool does not exist.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        pools = self.workspace.get_calculation_pools()
        submit_pool_id: int | None
        if pool_name and pool_id:
            raise _log_and_get_exception(RunParameterError, "Both pool_name and pool_id were provided.")
        elif not pool_name and not pool_id:
            submit_pool_id = self.project.default_pool_id if self.project.default_pool_id else pools[0].id
        elif pool_name:
            # Get the id of the matching pool
            submit_pool_id = next((pool.id for pool in pools if _casefold_equals(pool.name, pool_name)), None)
        elif pool_id:
            # Ensure the pool exists or assign None if it doesn't
            submit_pool_id = next((pool.id for pool in pools if pool.id == pool_id), None)

        if submit_pool_id is None:
            raise _log_and_get_exception(CalculationPoolNotFoundError, f"Pool {pool_id or pool_name} not found.")
        response = create_job.sync_detailed(
            workspace_id=self.workspace.id,
            client=self.connection._get_authenticated_client(),
            body=CreateJob.from_dict({"projectId": self.project.id, "runId": self.id, "poolId": submit_pool_id}),
        )
        raw_job: ClientJob = self._validate_response(response, JobResponse, ClientJob)

        return Job(raw_job, self.connection, self)

    def get_job(self) -> Union["Job", None]:
        """Gets the job information for the run if it is calculating or has been calculated, otherwise returns None.

        Returns:
            Job representing the calculation job that is in progress or has completed or None if the input data has
            been modified since the run was last calculated.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_run.sync_detailed(
            workspace_id=self.workspace.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_run: ClientRun = self._validate_response(response, RunResponse, ClientRun)
        if raw_run.job_id is None or isinstance(raw_run.job_id, Unset):
            return None

        response = get_job.sync_detailed(
            workspace_id=self.workspace.id,
            job_id=raw_run.job_id,
            client=self.connection._get_authenticated_client(),
        )
        raw_job: ClientJob = self._validate_response(response, JobResponse, ClientJob)

        return Job(raw_job, self.connection, self)

    def get_output_data(
        self,
        table_name: Unset | str = UNSET,
        pool: Unset | str = UNSET,
        pool_id: Unset | int = UNSET,
        wait_seconds: int = 0,
    ) -> dict | str:
        """Retrieves the run's output data, submitting a calculation if necessary.

        Warning:
            If the run has not been calculated, this will cause the run to be calculated on the specified pool.
            To retrieve results for a specific run without causing a calculation,
            use :py:func:`.get_run_result_table_data`.

        Specifying the table_name will return output data for that table only, otherwise all output tables will be
        returned.

        Note:
            You can convert this table to csv using :py:func:`.output_table_to_csv`. Alternatively, if you want to return all
            tables as a folder of csvs you can use :py:func:`.output_tables_to_folder`.

        Args:
            table_name (str | Unset): Output data table name. Defaults to UNSET.
            pool (str | Unset): Name of the pool to use for calculating. Defaults to UNSET. If no pool name is given the
                default pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id (int | Unset): Id of the pool to use for calculating. Defaults to UNSET. Can be used instead of
                pool_name, but both cannot be provided.
            wait_seconds (int): The number of seconds to wait for the run to complete. Defaults to 0.

        Returns:
            If table_name is UNSET, returns all output tables for a run as a dictionary.
            If table_name is specified, returns the specified output table as a dictionary.
            If the run status is not completed, returns a message indicating the run status.

        Raises:
            CalculationPoolNotFoundError: The specified pool does not exist.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """

        pools = self.workspace.get_calculation_pools()
        if pool and pool_id:
            raise _log_and_get_exception(RunParameterError, "Both pool_name and pool_id were provided.")
        elif not pool and not pool_id:
            submit_pool_id = self.project.default_pool_id if self.project.default_pool_name else pools[0].id
        elif pool:
            # Get the id of the matching pool
            submit_pool_id = next((calc_pool.id for calc_pool in pools if _casefold_equals(calc_pool.name, pool)), None)
        else:
            # Ensure the pool exists or assign None if it doesn't
            submit_pool_id = next((calc_pool.id for calc_pool in pools if calc_pool.id == pool_id), None)

        if submit_pool_id is None:
            raise _log_and_get_exception(CalculationPoolNotFoundError, f"Pool {pool_id or pool} not found.")
        response = get_output_data.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            table_name=table_name,
            pool_id=submit_pool_id,
            wait_seconds=wait_seconds,
            client=self.connection._get_authenticated_client(),
        )
        raw_output_data: OutputData = self._validate_response(response, OutputDataResponse, OutputData)
        result = raw_output_data.to_dict()

        if result["runStatus"] != "Done":
            if result["runStatus"] == "ModelError":
                message = f"Run status for {self.name} is model error: {result['modelError']}"
            else:
                message = f"Run status for {self.name} is: {result['runStatus']}"
            print(message)
            return message
        elif isinstance(table_name, Unset):
            return cast(dict, result["outputTables"])
        else:
            # retrieve the index based on case-folded equality
            return cast(
                dict,
                next(
                    (
                        table
                        for key, table in cast(dict, result["outputTables"]).items()
                        if _casefold_equals(key, table_name)
                    ),
                    None,
                ),
            )

    def get_child_runs(self) -> list["Run"]:
        """Returns the child runs of the run.

        Returns:
            List of child runs.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return [run for run in self.project.get_runs() if run.parent_id == self.id]

    def create_child_run(
        self, run_name: str, description: str = "", auto_delete_minutes: Optional[int] = None
    ) -> "Run":
        """Creates a child run of the run.

        Args:
            run_name: The name given to the child run. Maximum of 100 characters and must be unique across all other
                runs in this project.
            description: Description of the child run. Defaults to "".
            auto_delete_minutes: If supplied, indicates that we wish the system to automatically delete the run and all
                its data after the specified time in minutes has elapsed. Defaults to None.

        Returns:
            The newly created child run.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return self.project.create_run(run_name, self.id, description, auto_delete_minutes=auto_delete_minutes)

    def calculate_child_runs(self, pool_name: str = "", pool_id: int | None = None) -> None:
        """Starts child run jobs if they need calculating.

        Args:
            pool_name: Name of the pool to use for calculating. Defaults to "". If no pool name or id is given the first
                pool in the connection will be used.
            pool_id: Id of the pool to use for calculating. Defaults to None. Can be used instead of of pool_name.

        Raises:
            CalculationPoolNotFoundError: The specified pool does not exist.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        runs = self.get_child_runs()
        for run in runs:
            run.calculate(pool_name, pool_id)

    def delete_child_runs(self) -> None:
        """Deletes all child runs of the run.

        Raises:
            RunDeletionError: Run deletion failed.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        runs = self.get_child_runs()
        for run in runs:
            run.delete()

    def run_results_to_csv(
        self,
        folder_path: str,
        overwrite: bool = False,
    ) -> None:
        """Retrieves all run results and writes them to the given location as csvs.

        Args:
            folder_path: Folder path to write the csv files.
            overwrite: If True, existing csv files will be overwritten. Defaults to False.

        Raises:
            InvalidFileError: The csv file already exists.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received."""

        run_results = self.get_run_results()

        for run_result in run_results:
            if run_result.is_in_use:
                temp_run_result_folder = os.path.join(folder_path, run_result.name)
                os.makedirs(temp_run_result_folder, exist_ok=True)
                self._run_result_table_nodes_to_csv(
                    run_result.name, run_result.get_table_nodes(), temp_run_result_folder, overwrite
                )

    def _run_result_table_nodes_to_csv(
        self,
        run_result_name: str,
        run_result_table: list["RunResultTableNode"],
        target_path: str,
        overwrite: bool = False,
    ):
        os.makedirs(target_path, exist_ok=True)

        for node in run_result_table:
            if node.folder:
                subfolder_path = os.path.join(target_path, node.name)
                self._run_result_table_nodes_to_csv(run_result_name, node.children, subfolder_path, overwrite)
            else:
                # save table to csv
                csv_path = os.path.join(target_path, f"{node.name}.csv")
                if os.path.exists(csv_path):
                    if not overwrite:
                        raise _log_and_get_exception(
                            InvalidFileError, f"{csv_path} already exists. Please choose a different name."
                        )
                    else:
                        # if overwrite is True, delete the existing file
                        os.remove(csv_path)

                self.run_result_table_to_csv(run_result_name, node.name, csv_path)

    def run_result_table_to_csv(
        self,
        result_name: str,
        table_name: str,
        csv_name: Optional[str] = None,
    ) -> None:
        """Retrieves a result data table by name and outputs it to a csv file.

        Note:
            This method does not cause the run to be calculated. It retrieves results for a specific run
            without causing a calculation.

        Args:
            result_name: Name of the result.
            table_name: Output data table name.
            csv_name: Name given to the csv file. If not supplied, the csv file will be named after the table_name.

        Raises:
            InvalidFileError: The csv file already exists.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """

        if csv_name is None:
            csv_name = f"{table_name}.csv"

        if os.path.exists(csv_name):
            raise _log_and_get_exception(
                InvalidFileError, f"{csv_name} already exists. Please choose a different name."
            )

        result = self.get_run_result_table_data(table_name, result_name)

        fields = [dimension["name"] for dimension in result["dimensions"] + result["values"]]
        items = result["data"]
        with open(csv_name, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(fields)
            csv_writer.writerows(items)
        message = f"{table_name} written to {csv_name}"
        logger.info(message)
        print(message)

    def output_table_to_csv(
        self,
        table_name: str,
        csv_name: Optional[str] = None,
        pool_name: str | Unset = UNSET,
        pool_id: int | Unset = UNSET,
        wait_seconds: int = 0,
    ) -> None:
        """Retrieves an output data table by name and outputs it to a csv file, submitting a calculation if necessary.

        Warning:
            If the run has not been calculated, this will cause the run to be calculated on the specified pool.
            To retrieve results for a specific run without causing a calculation,
            use :py:func:`.run_result_table_to_csv`.

        Args:
            table_name: Output data table name.
            csv_name: Name given to the csv file. If not supplied, the csv file will be named after the table_name.
            pool_name: Name of the pool to use for calculating. Defaults to UNSET. If no pool name or id is given the
                default pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id: Id of the pool to use for calculating. Defaults to UNSET. Can be used instead of pool_name.
            wait_seconds: The number of seconds to wait for the run to complete. Defaults to 0.

        Raises:
            InvalidFileError: The csv file already exists.
            OutputDataTableError: Output data is unavailable.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if csv_name is None:
            csv_name = f"{table_name}.csv"

        if os.path.exists(csv_name):
            raise _log_and_get_exception(
                InvalidFileError, f"{csv_name} already exists. Please choose a different name."
            )

        table = self.get_output_data(table_name, pool=pool_name, pool_id=pool_id, wait_seconds=wait_seconds)
        if isinstance(table, str):
            raise _log_and_get_exception(OutputDataTableError, "Output data is unavailable.", table)
        else:
            self._convert_table_to_csv(table_name, table, csv_name)

    def output_tables_to_folder(
        self,
        folder_path: str,
        pool_name: str | Unset = UNSET,
        pool_id: int | Unset = UNSET,
        wait_seconds: int = 0,
    ) -> None:
        """Retrieves all output tables and writes them to the given location as csvs, submitting a calculation if necessary.

        Warning:
            If the run has not been calculated, this will cause the run to be calculated on the specified pool.
            To retrieve results for a specific run without causing a calculation,
            use :py:func:`.run_result_table_to_csv`.

        Args:
            folder_path: Folder path to write the csv files.
            pool_name: Name of the pool to use for calculating. Defaults to UNSET. If no pool name or id is given the
                default pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id: Id of the pool to use for calculating. Defaults to UNSET. Can be used instead of pool_name
            wait_seconds: The number of seconds to wait for the run to complete. Defaults to 0.

        Raises:
            FolderNotFoundError: The folder does not exist.
            OutputDataTableError: Output data is unavailable.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if not os.path.exists(folder_path):
            raise _log_and_get_exception(FolderNotFoundError, f"{folder_path} folder does not exist.")

        output_tables = self.get_output_data(pool=pool_name, pool_id=pool_id, wait_seconds=wait_seconds)

        if isinstance(output_tables, str):
            raise _log_and_get_exception(OutputDataTableError, "Output data is unavailable.", output_tables)

        for table_name, table in output_tables.items():
            csv_name = os.path.join(folder_path, f"{table_name}.csv")
            self._convert_table_to_csv(table_name, table, csv_name)

    @classmethod
    def compare_output_csvs(
        cls, output_csv1: str, output_csv2: str, tolerance: float = 0, suffixes: Union[None, list[str]] = None
    ) -> list[dict[str, Union[str, float]]]:
        """Compares two output csvs and returns the row differences as a list of dictionaries.

        Note:
            The csvs must have the same headers and the same number of rows for the comparison to work.
            Unmatched rows are also returned.

            If the values are strings, they are compared directly. A difference of 1.0 is returned if they are
            different, otherwise 0.0 is returned.

        Args:
            output_csv1: Path to the first output csv.
            output_csv2: Path to the second output csv.
            tolerance: Value that defines a difference. I.e only differences greater than this value will be
                counted. Defaults to 0.
            suffixes: Appended to the value column headers. Defaults to ["_1", "_2"].

        Returns:
            List of dictionaries where each dictionary is a row of data that was either different in value or unmatched.

            Example output::

                [
                    {"id": "1", "value_1": 1.0, "value_2": 2.0, "difference": -1.0, "abs difference": 1.0},
                    {
                        "id": "4",
                        "value_1": 40.0,
                        "value_2": math.nan,
                        "difference": math.nan,
                        "abs difference": math.nan,
                    },
                    {
                        "id": "6",
                        "value_1": math.nan,
                        "value_2": 70.0,
                        "difference": math.nan,
                        "abs difference": math.nan,
                    },
                ]


        Raises:
            FileNotFoundError: One or more files were not found.
            NonCsvFileError: Only csv files are accepted.
            RunParameterError: Suffixes must be a list of two strings to differentiate between the two csvs.
            KeyError: The csvs do not have the required 'Value' header.
            DataTransformationError: No headers were found in the csvs, or the headers in the csvs are different.
            UnexpectedResponseError: An unexpected API response was received.
            UnsuccessfulRequestError: API response was not successful."""
        if suffixes is None:
            suffixes = ["_1", "_2"]

        if len(suffixes) != 2:
            raise _log_and_get_exception(
                RunParameterError, "suffixes must be a list of two strings to differentiate between the two csvs."
            )

        table1, headers1 = cls._read_csv(output_csv1)
        table2, headers2 = cls._read_csv(output_csv2)

        if not headers1 or not headers2:
            print("No headers found in the csvs.")
            raise _log_and_get_exception(DataTransformationError, "No headers found in the csvs.")

        if headers1 != headers2:
            print("Headers of the two csvs are different. Please ensure they are the same.")
            raise _log_and_get_exception(
                DataTransformationError, "The headers of the two csvs are different. Please ensure they are the same."
            )

        table1_is_empty = all(row["Value"] == "" for row in table1)
        table2_is_empty = all(row["Value"] == "" for row in table2)

        if table1_is_empty and table2_is_empty:
            print("No differences found.")
            return []

        non_values = [header for header in headers1 if header != "Value"]
        joined_tables = cls._merge_tables(table1, table2, non_values, suffixes)

        for row in joined_tables:
            value1 = row.get(f"value{suffixes[0]}")
            value2 = row.get(f"value{suffixes[1]}")
            if isinstance(value1, str) or isinstance(value2, str):
                row["difference"] = row["abs difference"] = 1.0 if value1 != value2 else 0.0
            else:
                value1 = cast(float, value1)
                value2 = cast(float, value2)
                if math.isnan(value1) and math.isnan(value2):
                    row["difference"] = row["abs difference"] = 0.0
                else:
                    row["difference"] = value1 - value2
                    row["abs difference"] = abs(cast(float, row["difference"]))

        differences = [
            row
            for row in joined_tables
            if cast(float, row["abs difference"]) > tolerance or math.isnan(cast(float, row["difference"]))
        ]

        if len(differences) == 0:
            print("No differences found.")
        else:
            print(f"{len(differences)} differences found.")

        return differences

    @classmethod
    def compare_output_csvs_in_folder(
        cls, folder1: str, folder2: str, tolerance: float = 0, output_folder: Optional[str] = None
    ) -> list[list[Union[str, float, int]]]:
        """Compares output csvs across two folders.

        Note:
            Csvs are compared based on their file names.
            The csvs must have the same headers and the same number of rows for the comparison to work.
            Unmatched rows are also returned.

            If the values are strings, they are compared directly. A difference of 1.0 is returned if they are
            different, otherwise 0.0 is returned.

            If the headers do not match or does not contain a 'Value' the result of the comparison will be
            a NaN value for the absolute difference and the number of unmatched rows will be 1. A log message will be
            generated to indicate the error.

        Args:
            folder1: Path to the first folder containing output csvs. Treated as the reference folder for file names.
            folder2: Path to the second folder containing output csvs.
            tolerance: Value that defines a difference. I.e only differences greater than this value will be counted.
                Defaults to 0.
            output_folder: If output folder is specified the file comparison summaries and overall summary will be
                written here. Defaults to None.

        Returns:
            Summary of differences as a list of lists. Each list contains the file name, total absolute difference and
            the number of unmatched rows.

            Example output::

                [
                    ["file", "total abs difference", "unmatched rows"],
                    ["test_0.csv", 5.0, 2],
                    ["test_1.csv", 5.0, 4],
                ]

        Raises:
            FolderNotFoundError: One or more folders were not found.
            FileNotFoundError: One or more files were not found.
            NonCsvFileError: Only csv files are accepted.
            RunParameterError: Suffixes must be a list of two strings to differentiate between the two csvs.
            UnexpectedResponseError: An unexpected API response was received.
            UnsuccessfulRequestError: API response was not successful.
        """
        if output_folder and not os.path.exists(output_folder):
            raise _log_and_get_exception(FolderNotFoundError, f"{output_folder} folder does not exist.")

        if not os.path.exists(folder1):
            raise _log_and_get_exception(FolderNotFoundError, f"{folder1} folder does not exist.")

        if not os.path.exists(folder2):
            raise _log_and_get_exception(FolderNotFoundError, f"{folder2} folder does not exist.")

        # Get all the csv files recursively in folder1 and ensure there are exactly matching files in folder2.
        files = []
        for root, _, filenames in os.walk(folder1):
            for filename in filenames:
                # Get relative path from folder1 to maintain folder structure
                relative_path = os.path.relpath(os.path.join(root, filename), folder1)

                # Check if corresponding file exists in folder2 and if it's a CSV file
                corresponding_file = os.path.join(folder2, relative_path)
                if _validate_files_exist([corresponding_file]) and _validate_files_are_csv([filename]):
                    files.append(relative_path)

        summary: list[list[Union[str, float, int]]] = [["file", "total abs difference", "unmatched rows"]]
        for file in files:
            print(f"checking {file}")
            try:
                differences = cls.compare_output_csvs(
                    os.path.join(folder1, file),
                    os.path.join(folder2, file),
                    tolerance,
                    suffixes=[f"_{folder1}", f"_{folder2}"],
                )
            except KeyError as e:
                logger.error(f"Key error for {file}: {e}")
                summary += [[file, float("nan"), 1]]
                continue
            except DataTransformationError as e:
                logger.error(f"Data transformation error for {file}: {e}")
                summary += [[file, float("nan"), 1]]
                continue

            if output_folder and len(differences) > 0:
                # Create the full output path, maintaining directory structure
                output_file_path = os.path.join(output_folder, file)
                # Ensure the directory exists (only create if there are subdirectories)
                output_dir = os.path.dirname(output_file_path)
                if output_dir != output_folder:
                    os.makedirs(output_dir, exist_ok=True)

                with open(output_file_path, mode="w", newline="") as differences_file:
                    writer = csv.DictWriter(differences_file, fieldnames=differences[0].keys())
                    writer.writeheader()
                    writer.writerows(differences)
            summary += [
                [
                    file,
                    sum(
                        [
                            cast(float, row["abs difference"])
                            for row in differences
                            if not math.isnan(cast(float, row["abs difference"]))
                        ]
                    ),
                    sum([1 for row in differences if math.isnan(cast(float, row["abs difference"]))]),
                ]
            ]

        logger.info(f"summary of difference:\n{summary}")

        if output_folder:
            with open(file=f"{output_folder}\\summary.csv", mode="w", newline="") as summary_file:
                csv_writer = csv.writer(summary_file)
                csv_writer.writerows(summary)

        return summary

    def get_input_data_with_data_group_name(
        self,
        data_group_name: str,
        data_table_name: str,
    ) -> dict:
        """Retrieves input data for a given data group and table.

        Args:
            data_group_name: Name of the data group.
            data_table_name: Name of the input data table.

        Returns:
            A dictionary containing the requested input data table along with its metadata.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_data_table_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            data_group_name=data_group_name,
            data_table_name=data_table_name,
            client=self.connection._get_authenticated_client(),
        )
        raw_table_data: TableData = self._validate_response(response, TableDataResponse, TableData)

        return raw_table_data.to_dict()

    def get_run_results(self) -> list["RunResult"]:
        """Retrieves all run results for the run.

        Returns:
            A list containing all run results for the run. Each run result the property is_in_use which can be used to
            determine if the run result contains data in the run result tables.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_run_results_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_run_results: list[ClientRunResult] = self._validate_response(
            response, RunResultArrayResponse, ClientRunResult
        )

        return [RunResult(self, raw_run_result.to_dict()) for raw_run_result in raw_run_results]

    def get_run_result_table_nodes(self, run_result_name: str) -> list["RunResultTableNode"]:
        """Retrieves all result tables for a given run result.

        Args:
            run_result_name: Name of the result.

        Returns:
            A list containing all result tables for the given run result. Each node may be a table or a
            group containing tables or other groups.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_result_tables_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            run_result_name=run_result_name,
            client=self.connection._get_authenticated_client(),
        )
        raw_result_tables: list[ClientResultTableNode] = self._validate_response(
            response, ResultTableNodeArrayResponse, ClientResultTableNode
        )

        return [
            RunResultTableNode(self, run_result_name, raw_result_table.to_dict())
            for raw_result_table in raw_result_tables
        ]

    def get_run_result_table_data(self, table_name: str, result_name: str) -> dict:
        """Retrieves result data for a given run result and table, only if the run has been calculated.

        Note:
            This method does not cause the run to be calculated. It is used to retrieve results for a specific run
            without causing a calculation.

        Args:
            table_name: Name of the result data table.
            result_name: Name of the result.

        Returns:
            A dictionary containing the requested result data table along with its metadata.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_result_table_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            run_result_name=result_name,
            result_table_name=table_name,
            client=self.connection._get_authenticated_client(),
        )
        raw_table_data: OutputData = self._validate_response(response, TableDataResponse, TableData)

        return raw_table_data.to_dict()

    def get_input_data(self, data_table_name: str) -> dict[str, Any]:
        """Retrieves input data for a given table in a form accepted by post_input_data.

        Args:
            data_table_name: Name of the data table.

        Returns:
            A dictionary containing the requested input data table.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_input_data_for_table.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            data_table_name=data_table_name,
            client=self.connection._get_authenticated_client(),
        )
        raw_input_data: InputData = self._validate_response(response, InputDataResponse, InputData)

        return cast(dict[str, Any], raw_input_data.to_dict()["data"])

    def post_input_data(self, data: dict[str, Any], data_limit: int = 10000) -> None:
        """Updates input data table(s).

        Args:
            data: Dictionary containing the input data table(s) to update.
            data_limit: Limit on the number of tables to update. If the limit is exceeded a warning will be logged.
                Defaults to 10000.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        if self._dict_count(data) > data_limit:
            logger.warning(
                "Warning. Data may be too large to input in this form.\
                Try splitting it into smaller chunks."
            )
        response: Response[Any] = update_input_data.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
            body=UpdateInputData.from_dict(data),
        )
        self._check_response_is_valid(response)
        _ensure_runs_are_processed([self], self.connection._run_processing_minutes)

    def post_input_table(self, table_data: dict[str, Any], table_name: str) -> None:
        """Updates a single input data table, splitting into multiple requests if necessary

        Args:
            table_data: Dictionary containing the data to post to the input table.
            table_name: Name of the table to update.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        batch_size = self.connection.post_data_row_batch_size
        row_count = len(list(table_data.values())[0])
        for start in range(0, row_count, batch_size):
            data: dict[str, Any] = {"tableUpdates": {}}
            data["tableUpdates"][table_name] = {
                key: value[start : start + batch_size] for key, value in table_data.items()
            }
            self.post_input_data(data)

    def upload_files_to_table(
        self,
        *files_and_descriptions: Union[str, tuple[str, str]],
        table_name: str,
        column_name: str,
        **dimension_column_and_values: list[str],
    ) -> dict[str, "UploadedFile"]:
        """Uploads files and adds them to a specified table column.

        Args:
            *files_and_descriptions: Files to upload to Igloo Cloud and related descriptions. Descriptions default to
                empty strings if only file paths are passed in.
            table_name: Name of table.
            column_name: Name of the column.
            **dimension_column_and_values: Required for specifying rows within multi-dimensional data tables.

        Returns:
            Map of uploaded file names to the corresponding uploaded file in Igloo Cloud.

        Raises:
            FileNotFoundError: One or more of the files were not found.
            NonCsvFileError: Only csv files are accepted.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.

        Example:
            >>> upload_files_to_table(
                ("file.csv", "Some file description"),
                table_name="Table1",
                column_name="Column1",
                Dimension1=["Value3"],
                Dimension2=["Value1"],
            )
        """
        uploaded_files = self.workspace.upload_files(*files_and_descriptions)
        uploaded_file_names = [uploaded_file.name for uploaded_file in uploaded_files.values()]
        table_updates = dimension_column_and_values | {column_name: uploaded_file_names}
        self.post_input_table(table_updates, table_name)
        return uploaded_files

    def delete(self) -> None:
        """Deletes the run in Igloo Cloud.

        Raises:
            RunDeletionError: Run deletion failed.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if (
            self.cached_finalization_state == RunFinalizationState.FINALIZED
            or self.cached_finalization_state == RunFinalizationState.FINALIZING
            or self.cached_finalization_state == RunFinalizationState.FINALIZATIONREQUESTED
        ):
            raise RunDeletionError(
                f"Cannot delete run that has finalization state: {self.cached_finalization_state}", None
            )
        response = delete_run_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        self._validate_response(response, DeleteRunResultResponse, DeleteRunResult)

        logger.info(f"Run {self.name} was successfully deleted.")

    def finalize(self) -> None:
        """Finalizes the run in Igloo Cloud.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        if self.cached_finalization_state is RunFinalizationState.FINALIZED:
            return
        body = update_run_finalization_state.UpdateRunFinalizationState(RunFinalizationState.FINALIZATIONREQUESTED)
        response = update_run_finalization_state.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            body=body,
            client=self.connection._get_authenticated_client(),
        )

        self._check_response_is_valid(response)
        self.cached_finalization_state = RunFinalizationState.FINALIZING

    def edit_name_or_description(self, name: Union[Unset, str] = UNSET, description: Union[Unset, str] = UNSET) -> None:
        """Edits the name or description of the run.

        Args:
            name: New name for the run. Leave blank to keep current name. Defaults to UNSET.
            description : New description for the run. Leave blank to keep current description. Defaults to UNSET.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = update_run_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            client=self.connection._get_authenticated_client(),
            body=UpdateRun(name=name, description=description),
        )
        self._check_response_is_valid(response)

        self.name = self.name if isinstance(name, Unset) else name
        self.description = self.description if isinstance(description, Unset) else description

        logger.info(
            (
                f"{f'Run name was successfully updated to {name}.' if name is not UNSET else ''}\n"
                f"{f'Run description was successfully updated to {description}.' if description is not UNSET else ''}"
            )
        )

    def odata_get_data_table(self, table_name: str, **kwargs) -> list[dict]:
        """Retrieves a data table with the given name via the OData endpoint.

        Args:
            table_name: Full name of table to get data from.
            **kwargs: OData operations `filter_`, `select`, `orderby`, `top`, `skip` and `count`.

        Returns:
            A list of dictionaries where each dictionary is a row of data within the table and includes the version id
            for that row.

            Example output::

                [
                    {"Version": "686t1", "UDSimple": "User 1", "Value": 2.0},
                    {"Version": "686t1", "UDSimple": "User 1", "Value": 0.25},
                    {"Version": "686t1", "UDSimple": "User 1", "Value": 0.75},
                ]

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = get_o_data_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.project.id,
            run_id=self.id,
            table_name=table_name,
            client=self.connection._get_authenticated_client(),
            **kwargs,
        )
        self._check_response_is_valid(response)
        values = cast(list[GetODataForRunResponse200ValueItem], cast(GetODataForRunResponse200, response.parsed).value)

        return [value.additional_properties for value in values]

    def copy_table_from_run(self, run_to_copy_from: "Run", data_table_name: str) -> None:
        """Copies a table from another run.

        Args:
            run_to_copy_from: Run to copy the table from.
            data_table_name: Name of the table to copy.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        logger.info(f"copying {data_table_name} from {run_to_copy_from.name} to {self.name}")
        self.post_input_table(run_to_copy_from.get_input_data(data_table_name), data_table_name)

    def copy_data_group_from_run(
        self,
        run_to_copy_from: "Run",
        data_group_name: str,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> None:
        """Copies a data group from another run.

        Args:
            run_to_copy_from: Run to copy the data group from.
            data_group_name: Name of the data group to copy.
            folder_path: Optional folder path to upload files from. Defaults to None. Note that files in the
                alternate workspace take priority over files in the folder_path.
            resolve_file_callback: Optional function for handling file references during cross-workspace copying.
                Accepts (original_file, existing_file, folder_path, workspace, logger) and returns the file name to use.
                Default resolution policy: check if file already exists in alternate workspace, then try uploading from
                folder_path if provided, otherwise leave reference blank and log a warning.

        Raises:
            ProjectHasNoRunsError: There are no runs in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """

        resolve_file_callback = resolve_file_callback or default_file_reference_copy_policy

        table_names = [table["name"] for table in self.project.get_data_tables_in_data_group(data_group_name)]
        data: dict[str, Any] = {"tableUpdates": {}}

        # Set the files to None so they are only loaded if needed.
        existing_files = None
        original_files = None

        for table_name in table_names:
            data["tableUpdates"][table_name] = self._get_table_update(
                run_to_copy_from,
                table_name,
                data_group_name,
                resolve_file_callback,
                folder_path,
                existing_files,
                original_files,
            )

        # First try to update the whole datagroup in one go, as this is most efficient for small to medium size data sets
        logger.info(f"copying {data_group_name} from {run_to_copy_from.name} to {self.name}")
        try:
            self.post_input_data(data)
            return
        except UnsuccessfulRequestError as error:
            if error.status_code in [
                HTTPStatus.SERVICE_UNAVAILABLE,
                HTTPStatus.GATEWAY_TIMEOUT,
                HTTPStatus.REQUEST_TIMEOUT,
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            ]:
                logger.info(
                    f"{error.status_code} response trying to copy the data group in one go. Will retry copying one table at a time."
                )
                # Drop down to copy the data table by table
            else:
                raise error

        # Second attempt, update one table at a time, requeueing any tables that fail in the first attempt in case they require later tables to be updated first
        retry_table_names = []
        for table_name in table_names:
            try:
                self.post_input_table(data["tableUpdates"][table_name], table_name)
            except UnsuccessfulRequestError as error:
                if error.status_code == HTTPStatus.CONFLICT:
                    retry_table_names.append(table_name)
                    logger.info(f"{error.status_code} response trying to copy {table_name}. Will retry at the end.")
                else:
                    raise error

        for table_name in retry_table_names:
            self.post_input_table(data["tableUpdates"][table_name], table_name)

    def _get_table_update(
        self,
        run_to_copy_from: "Run",
        table_name: str,
        data_group_name: str,
        resolve_file_callback: "FileReferenceCopyPolicy",
        folder_path: str | None,
        existing_files: list["UploadedFile"] | None,
        original_files: list["UploadedFile"] | None,
    ):
        table_update = run_to_copy_from.get_input_data(table_name)
        table_def = self.project.get_data_table_metadata(table_name, data_group_name)

        # If the workspaces are the same, file references will work automatically
        if self.workspace == run_to_copy_from.workspace:
            return table_update

        # This for loop handles references to files
        for column in (*table_def.dimensions, *table_def.values):
            if column.data_type != DataType.FILE:
                continue
            for index, file_name in enumerate(table_update[column.name]):
                if file_name == "":
                    continue
                if existing_files is None:
                    existing_files = self.workspace.get_uploaded_files()
                if original_files is None:
                    original_files = run_to_copy_from.workspace.get_uploaded_files()
                existing_file = next((file for file in existing_files if file.name == file_name), None)
                original_file = next(file for file in original_files if file.name == file_name)
                table_update[column.name][index] = resolve_file_callback(
                    original_file, existing_file, folder_path, self.workspace, logger
                )
        return table_update

    def copy_run_from_run(
        self,
        run_to_copy_from: "Run",
        only_copy_owned_datagroups: bool = False,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> None:
        """Copies all the data groups from another run.

        Args:
            run_to_copy_from: Run to copy the data groups from.
            only_copy_owned_datagroups: If True, only copy data groups owned by the run. Defaults to False.
            folder_path: Optional folder path to upload files from. Defaults to None. Note that files in the
                alternate workspace take priority over files in the folder_path.
            resolve_file_callback: Optional function for handling file references during cross-workspace copying.
                Accepts (original_file, existing_file, folder_path, workspace, logger) and returns the file name to use.
                Default resolution policy: check if file already exists in alternate workspace, then try uploading from
                folder_path if provided, otherwise leave reference blank and log a warning.

        Raises:
            ProjectHasNoRunsError: There are no runs in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        for data_group in run_to_copy_from.get_data_groups():
            if only_copy_owned_datagroups and "ownerRunIfNotOwned" in data_group.keys():
                continue
            self.copy_data_group_from_run(run_to_copy_from, data_group["name"], folder_path, resolve_file_callback)

    def copy_run(
        self,
        new_run_name: Optional[str] = None,
        project: Optional["Project"] = None,
        parent_id: Optional[int] = None,
        only_copy_owned_datagroups: bool = False,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> "Run":
        """Copies run.

        Args:
            new_run_name: Run copy name. Maximum of 100 characters and must be unique across all other runs in the
                project. Defaults to None.
            project: Project to create the copy in. Defaults to None.
            parent_id: Specifies the parent run. Only allowed for copying into a different project. Defaults to None.
            only_copy_owned_datagroups: If True, only copy data groups owned by the run. Defaults to False.
            folder_path: Optional folder path to upload files from. Defaults to None. Note that files in the
                alternate workspace take priority over files in the folder_path.
            resolve_file_callback: Optional function for handling file references during cross-workspace copying.
                Accepts (original_file, existing_file, folder_path, workspace, logger) and returns the file name to use.
                Default resolution policy: check if file already exists in alternate workspace, then try uploading from
                folder_path if provided, otherwise leave reference blank and log a warning.

        Returns:
            Newly created copy of the run.

        Raises:
            RunNamingError: Copied runs require a different name or project from the original.
            RunParameterError: Parent id can only be set for a new project.
            ProjectHasNoRunsError: There are no runs in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        if new_run_name is None and project is None:
            raise _log_and_get_exception(
                RunNamingError, "Copied runs require a different name or project from the original."
            )

        if not project and parent_id:
            raise _log_and_get_exception(RunParameterError, "Parent id can only be set for a new project.")

        description = f"Copied from {self.name} in {self.project.name}"

        if project and not parent_id:
            project.get_base_run().copy_run_from_run(
                self, only_copy_owned_datagroups, folder_path, resolve_file_callback
            )
            return project.get_base_run()
        elif not new_run_name and project and parent_id:
            new_run = project.create_run(
                self.name, parent_id, description, auto_delete_minutes=self.auto_delete_minutes
            )
            new_run.copy_run_from_run(self, only_copy_owned_datagroups, folder_path, resolve_file_callback)
            return new_run
        elif new_run_name and project and parent_id:
            new_run = project.create_run(
                new_run_name, parent_id, description, auto_delete_minutes=self.auto_delete_minutes
            )
            new_run.copy_run_from_run(self, only_copy_owned_datagroups, folder_path, resolve_file_callback)
            return new_run
        else:
            return self._copy_run_into_new_child(
                cast(str, new_run_name), description, only_copy_owned_datagroups, folder_path, resolve_file_callback
            )

    def adjust_run(
        self,
        adjustment_dict: "RunAdjustmentDict",
        child_run_name: str = "",
        auto_delete_minutes: Optional[int] = None,
    ) -> "Run":
        """Adjusts the run's input data according to the given adjustment dictionary.

        Specifying a child run name will create a new child run with the adjustments instead of adjusting this run.
        Method allows for multiple tables and columns to be adjusted at once.

        Note:
            Filtering allows for the selection of rows to adjust within a table. Please see the examples for more info.

        Args:
            adjustment_dict: Dictionary containing the adjustments to be made to the run's input data.
            child_run_name: Specifying a child run name will create a new run with the adjustments. Defaults to "".
            auto_delete_minutes: Can only be set for new child runs. Indicates that we wish the system to automatically
                delete the run and all its data after the specified time in minutes has elapsed. Defaults to None.

        Returns:
            The adjusted run or if a child run name is given, the newly created child run with the adjustments.

        Raises:
            RunInputDictionaryKeyError: The given run adjustment dictionary contains an invalid key.
            RunInputDictionaryValueError: The given run adjustment dictionary contains an invalid value.
            RunInputDictionaryTypeError: The given run adjustment dictionary contains an invalid type.
            RunParameterError: Auto delete minutes can only be set for new child runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.

        Example:
            >>> run.adjust_run(
            {
                "Table_Name": {
                    "columns": {
                        "columnName1": {"function": lambda x: x * 100},
                        "columnName2": {"function": lambda x: x + 1},
                    },
                    "filter": lambda x: x["dimensionName"] <= 33,
                }
            }
        )
        """
        self._validate_input(adjustment_dict, RunAdjustmentDictValidator)
        if child_run_name is None and auto_delete_minutes:
            raise _log_and_get_exception(RunParameterError, "Auto delete minutes can only be set for new child runs.")

        adjusted_input_data, description = self._adjust_tables(adjustment_dict)

        run = self.create_child_run(child_run_name, description, auto_delete_minutes) if child_run_name else self
        run.post_input_data(adjusted_input_data)

        return run

    def create_sensitivity_runs(
        self,
        sensitivity_dict: "SensitivityDict",
        auto_delete_minutes: Optional[int] = None,
    ) -> list["Run"]:
        """Creates sensitivity runs based on the given sensitivity dictionary.

        Within a scenario, multiple tables can be adjusted at once. Each table can have multiple columns adjusted.
        Filtering allows for the selection of rows to adjust within a table.

        Note:
            Within a scenario, the number of factors must remain consistent across all tables and columns.

        Args:
            sensitivity_dict: Dictionary containing the scenarios.
            auto_delete_minutes: Indicates that we wish the Igloo Cloud to automatically delete the sensitivity runs and
                their data after the specified time in minutes has elapsed. Defaults to None.

        Returns:
            List of newly created sensitivity runs.

        Raises:
            RunInputDictionaryValueError: The given run sensitivity dictionary contains an invalid value.
            RunInputDictionaryTypeError: The given run sensitivity dictionary contains an invalid type.
            RunParameterError: Auto delete minutes can only be set for new child runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.

        Example:
            >>> run.create_sensitivity_runs(
            {
                "Scenario": {
                    "Table_Name1": {
                        "columns": {
                            "columnName1": {"factors": [1, 19, 22], "function": lambda x, factor: x + factor},
                            "columnName2": {"factors": [1.1, 1.15, 1.2], "function": lambda x, factor: x * factor}
                        },
                    },
                    "Table_Name2": {
                        "columns": {
                            "columnName3": {"factors": [8, 11, 12], "function": lambda x, factor: x + factor}
                            }
                    }
                }
            }
        )
        """
        self._validate_input(sensitivity_dict, SensitivityDictValidator)

        runs: list[Run] = []
        for scenario_name, table_sensitivity_dict in sensitivity_dict.items():
            runs += [
                self.adjust_run(scenario_run_adjustment_dict, child_run_name, auto_delete_minutes)
                for scenario_run_adjustment_dict, child_run_name in zip(
                    self._get_scenario_run_adjustments(table_sensitivity_dict),
                    self._get_child_run_names(scenario_name, table_sensitivity_dict),
                )
            ]

        return runs

    def _adjust_tables(self, adjustment_dict: "RunAdjustmentDict") -> tuple[dict[str, Any], str]:
        adjusted_input_data: dict[str, Any] = {"tableUpdates": {}, "replaceListTables": True}
        description = f"Based on {self.name}.\nAdjusted tables: "

        for i, (table_name, table_adjustment_dict) in enumerate(adjustment_dict.items()):
            input_data = self.get_input_data(table_name)
            row_masks = self._get_row_masks(
                input_data, cast(Callable, table_adjustment_dict.get("filter", lambda x: True))
            )
            # Using the potentially incorrect case here doesn't matter as it's posted the API which is case-insensitive
            adjusted_input_data["tableUpdates"][table_name] = self._apply_column_adjustments(
                table_name, table_adjustment_dict, input_data, row_masks
            )
            description += f"{table_name}, " if i < len(adjustment_dict) - 1 else f"{table_name}."

        return adjusted_input_data, description

    def _convert_table_to_csv(self, table_name: str, table: dict, csv_name: str) -> None:
        fields = list(table.keys())
        items = ([table[key][i] for key in table] for i in range(len(table[fields[0]])))
        with open(csv_name, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(fields)
            csv_writer.writerows(items)
        message = f"{table_name} written to {csv_name}"
        logger.info(message)
        print(message)

    def _copy_run_into_new_child(
        self,
        new_child_run_name: str,
        description: str,
        only_copy_owned_datagroups: bool = False,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> "Run":
        new_child_run = self.create_child_run(
            new_child_run_name,
            description,
            auto_delete_minutes=self.auto_delete_minutes,
        )
        new_child_run.copy_run_from_run(self, only_copy_owned_datagroups, folder_path, resolve_file_callback)
        return new_child_run

    def _get_child_run_names(
        self, scenario_name: str, table_sensitivity_dict: dict[str, "TableSensitivityDict"]
    ) -> list[str]:
        return [
            f"{self.name}-{scenario_name}-factor_{i + 1}"
            for i in range(self._get_number_of_factors(table_sensitivity_dict))
        ]

    @classmethod
    def _apply_column_adjustments(
        cls,
        table_name: str,
        table_adjustment_dicts: "TableAdjustmentDict",
        input_data: dict[str, Any],
        row_masks: list[bool],
    ) -> dict[str, Any]:
        for column_name, column_adjustment_dict in table_adjustment_dicts["columns"].items():
            # Find the real column name in the input data that matches the case-insensitive column name
            real_column_name = next((key for key in input_data.keys() if _casefold_equals(key, column_name)), None)
            if real_column_name is None:
                raise _log_and_get_exception(
                    RunInputDictionaryKeyError,
                    f"Column {column_name} not found in table {table_name}.",
                )
            input_data[real_column_name] = cls._adjust_column_values(
                row_masks,
                input_data[real_column_name],
                column_adjustment_dict["function"],
            )

        return input_data

    @classmethod
    def _get_row_masks(cls, data_table: dict[str, list[int]], filter: Callable) -> list[bool]:
        row_masks = [filter(row) for row in cls._transpose_table(data_table)]

        if not any(row_masks):
            raise _log_and_get_exception(
                DataTransformationError,
                "No rows match the filter. Please edit the filter to allow at least one row.",
            )
        else:
            return row_masks

    @classmethod
    def _get_scenario_run_adjustments(
        cls, table_sensitivity_dict: dict[str, "TableSensitivityDict"]
    ) -> list["RunAdjustmentDict"]:
        scenario_adjustment_dicts: list["RunAdjustmentDict"] = [
            {
                table_name: {
                    "columns": {},
                    "filter": cast(Callable, column_sensitivity_dict.get("filter", lambda x: True)),
                }
                for table_name, column_sensitivity_dict in table_sensitivity_dict.items()
            }
            for _ in range(cls._get_number_of_factors(table_sensitivity_dict))
        ]

        return cls._populate_run_adjustment_dicts_per_factor(table_sensitivity_dict, scenario_adjustment_dicts)

    @staticmethod
    def _adjust_column_values(
        row_masks: list[bool],
        column_data: list[Any],
        function: "OperatorFunction",
    ) -> list[Any]:
        return [function(value) if adjust_row else value for value, adjust_row in zip(column_data, row_masks)]

    @staticmethod
    def _dict_count(d: dict) -> int:
        return sum([Run._dict_count(v) if isinstance(v, dict) else 1 for v in d.values()])

    @staticmethod
    def _get_number_of_factors(table_sensitivity_dict: dict[str, "TableSensitivityDict"]) -> int:
        first_table = next(iter(table_sensitivity_dict.values()))
        first_column = next(iter(first_table["columns"].values()))
        factors = first_column["factors"]
        return len(factors)

    @staticmethod
    def _get_id_dim_dict(dim_table: dict[str, Any]) -> dict:
        for i, col in enumerate(dim_table["values"]):
            if col["displayName"] == "Id":
                id_column = i
            elif col["name"] == "Value":
                value_column = i
        output = {i[id_column]: i[value_column] for i in dim_table["data"]}
        return output

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global Job, RunResult, RunResultTableNode, UploadedFile
        from wtwco_igloo import Job, RunResult, RunResultTableNode, UploadedFile

    @staticmethod
    def _parse_value(value: str) -> Union[str, float]:
        """Parse a string value to its appropriate type (float, or str).

        Args:
            value: String value to parse

        Returns:
            If the value is an empty string, returns NaN (not a number).
            If the value can be parsed as a float, returns the float value.
            Else, returns the original string value.
        """
        if value == "":
            return math.nan

        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            # Return as string if not a number
            return value

    @classmethod
    def _merge_tables(
        cls, table1: list[dict[str, str]], table2: list[dict[str, str]], non_values: list[str], suffixes: list[str]
    ) -> list[dict[str, Union[str, float]]]:
        merged: list[dict[str, Union[str, float]]] = []
        matched_table2_rows: list[bool] = [False] * len(table2)
        for row1 in table1:
            match_found = False
            for i, row2 in enumerate(table2):
                if not matched_table2_rows[i] and all(row1[nv] == row2[nv] for nv in non_values):
                    merged_row: dict[str, Union[str, float, bool]] = {nv: row1[nv] for nv in non_values}
                    merged_row[f"value{suffixes[0]}"] = cls._parse_value(row1["Value"]) if "Value" in row1 else math.nan
                    merged_row[f"value{suffixes[1]}"] = cls._parse_value(row2["Value"]) if "Value" in row2 else math.nan
                    merged.append(merged_row)
                    matched_table2_rows[i] = True
                    match_found = True
                    break
            if not match_found:
                merged.append(cls._merge_unmatched_row(row1, non_values, suffixes))

        for i, row2 in enumerate(table2):
            if not matched_table2_rows[i]:
                merged.append(cls._merge_unmatched_row(row2, non_values, suffixes, table1=False))

        return merged

    @classmethod
    def _merge_unmatched_row(
        cls, unmatched_row: dict[str, str], non_values: list[str], suffixes: list[str], table1: bool = True
    ) -> dict[str, Union[str, float, bool]]:
        merged_row: dict[str, Union[str, float, bool]] = {nv: unmatched_row[nv] for nv in non_values}
        merged_row[f"value{suffixes[0]}"] = (
            cls._parse_value(unmatched_row["Value"]) if ("Value" in unmatched_row and table1) else math.nan
        )
        merged_row[f"value{suffixes[1]}"] = (
            cls._parse_value(unmatched_row["Value"]) if ("Value" in unmatched_row and not table1) else math.nan
        )
        return merged_row

    @staticmethod
    def _populate_run_adjustment_dicts_per_factor(
        table_sensitivity_dict: dict[str, "TableSensitivityDict"], scenario_adjustment_dicts: list["RunAdjustmentDict"]
    ) -> list["RunAdjustmentDict"]:
        for table_name, column_sensitivity_dict in table_sensitivity_dict.items():
            for column_name, column_sensitivity in column_sensitivity_dict["columns"].items():
                for i, factor in enumerate(column_sensitivity["factors"]):
                    scenario_adjustment_dicts[i][table_name]["columns"][column_name] = {
                        "function": _create_adjustment_function(column_sensitivity["function"], factor)
                    }
        return scenario_adjustment_dicts

    @staticmethod
    def _read_csv(file_path: str) -> tuple[list[dict[str, str]], Optional[list[str]]]:
        _validate_files_exist([file_path])
        _validate_files_are_csv([file_path])
        with open(file_path, mode="r") as file:
            reader = csv.DictReader(file)
            return [row for row in reader], cast(list[str], reader.fieldnames)

    @staticmethod
    def _transpose_table(data_table: dict[str, list[int]]) -> Generator[dict[str, list[Optional[int]]], None, None]:
        return (dict(zip(data_table.keys(), row)) for row in zip(*data_table.values()))
