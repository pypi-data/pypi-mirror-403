import csv
import os
from typing import TYPE_CHECKING, Any, Optional, Union, cast
from urllib.parse import urljoin

from wtwco_igloo.api_client.api.data_table import get_data_table_for_run
from wtwco_igloo.api_client.api.data_tables import list_data_tables_for_run
from wtwco_igloo.api_client.api.o_data import get_o_data_for_project
from wtwco_igloo.api_client.api.projects import delete_project
from wtwco_igloo.api_client.api.projects import update_project as update_project
from wtwco_igloo.api_client.api.result_table import get_result_table_for_run
from wtwco_igloo.api_client.api.runs import create_run_for_project, get_run_for_project, list_runs_for_project
from wtwco_igloo.api_client.models import (
    CreateRun,
    DataTableInclude,
    DataTableNode,
    DataTableNodeArrayResponse,
    GetODataForProjectResponse200,
    GetODataForProjectResponse200ValueItem,
    ProjectResponse,
    RunArrayResponse,
    RunResponse,
    TableDataResponse,
    UpdateProject,
)
from wtwco_igloo.api_client.models import Project as ClientProject
from wtwco_igloo.api_client.models import Run as ClientRun
from wtwco_igloo.api_client.models import TableData as ClientTableData
from wtwco_igloo.api_client.types import UNSET, Unset
from wtwco_igloo.extensions.table_definition import TableDefinition
from wtwco_igloo.extensions.utils.callbacks.run_callbacks import FileReferenceCopyPolicy
from wtwco_igloo.extensions.utils.documentation_fetcher import _DocumentationFetcher
from wtwco_igloo.extensions.utils.errors.model_errors import ModelNotFoundError
from wtwco_igloo.extensions.utils.errors.project_errors import (
    DataTableNotFoundError,
    ProjectDeletionError,
    ProjectHasNoRunsError,
    ProjectNamingError,
    ProjectParameterError,
)
from wtwco_igloo.extensions.utils.errors.run_errors import RunNotFoundError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception
from wtwco_igloo.extensions.utils.helpers import _casefold_equals, _ensure_runs_are_processed
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator
from wtwco_igloo.logger import logger

if TYPE_CHECKING:
    from wtwco_igloo import Model, Run, Workspace


class Project(object):
    """Represents a project in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the project.
        workspace (Workspace): Workspace containing the project.
        name (str): Name of the project.
        description (str): Description of the project.
        model_version_id (int): Identifier value of the model version used by the project.
        model (Model): Model used by the project.
        connection (Connection): Connection object used to authenticate with Igloo Cloud.
        default_pool_name (str): Name of the default pool used for calculations.
        default_pool_id (int): Id of the default pool used for calculations.
        contains_finalized_runs (bool): Whether or not the project has any runs that are finalized or finalizing.
        web_app_url (str): URL to the Igloo Cloud project.
    """

    def __init__(self, workspace: "Workspace", project: dict) -> None:
        self.id: int = project["id"]
        self.workspace: Workspace = workspace
        self.name: str = project["name"]
        self.description: str = project["description"] or ""
        self.model_version_id: int = project["modelVersionId"]
        self.default_pool_name: str = project.get("defaultPool") or ""
        self.default_pool_id: int | None = project.get("defaultPoolId")
        self.contains_finalized_runs: bool | None = project.get("containsFinalizedRuns")
        self.connection = workspace.connection
        self.web_app_url: str = urljoin(workspace.web_app_url, f"projects/{self.id}/")
        self._base_run: "Run" | None = None
        self._data_group_names: list[str] = []
        self._documentation_fetcher = _DocumentationFetcher(workspace.connection)
        self.__tables: dict[str, dict] = {}
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid
        self._validate_response = _ResponseValidator._validate_response
        self._import_classes()

    # Lazy population of the model attribute
    @property
    def model(self) -> "Model":
        if not hasattr(self, "_model"):
            self._model = next((model for model in self.workspace.get_models() if model.id == self.model_version_id))
        return self._model

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Project):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.model_version_id == other.model_version_id
            and self.description == other.description
            and self.default_pool_id == other.default_pool_id
            and self.workspace.id == other.workspace.id
        )

    def __str__(self) -> str:
        return f"id: {self.id}, name: {self.name}"

    def calculate_all_runs(self, pool_name: str | None = None, pool_id: int | None = None) -> None:
        """Calculates all runs in the project.

        Args:
            pool_name: Name of the pool to use for calculating. If no pool name is given the default
                pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id: Id of the pool to use for calculating. Can be used instead of pool_name.

        Raises:
            CalculationPoolNotFoundError: The specified pool does not exist.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        for run in self.get_runs():
            run.calculate(pool_name=pool_name, pool_id=pool_id)

    def copy_project(
        self,
        new_project_name: Optional[str] = None,
        new_description: Optional[str] = None,
        model_version_id: Optional[int] = None,
        alternate_workspace: Optional["Workspace"] = None,
        default_pool_name: Optional[str] = None,
        default_pool_id: Optional[int] = None,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> "Project":
        """Copies project.

        Args:
            new_project_name: Project copy name. Maximum of 100 characters and must be unique. Defaults to None. Note if
                no name is passed the method will create a project with the name: {original_project_name} - Copy.
            new_description: Project copy description. Defaults to None.
            model_version_id: Id of model to use for project copy. Defaults to None.
            alternate_workspace: Workspace to copy the project to, can be in a different environment. Set to None to
                use this projects workspace. Defaults to None.
            default_pool_name: Name of the pool to use for calculating. Defaults to None.
            default_pool_id: Id of the pool to use for calculating. Defaults to None. Can be used instead
                of default_pool_name
            folder_path: Optional folder path to upload files from. Defaults to None. Note that files in the
                alternate workspace take priority over files in the folder_path.
            resolve_file_callback: Optional function for handling file references during cross-workspace copying.
                Accepts (original_file, existing_file, folder_path, workspace, logger) and returns the file name to use.
                Default resolution policy: check if file already exists in alternate workspace, then try uploading from
                folder_path if provided, otherwise leave reference blank and log a warning.

        Returns:
            Newly created copy of the project.

        Raises:
            ProjectNamingError: Name of the project copy must be different from the original project.
            RunNotFoundError: Project has no runs.
            ModelNotFoundError: Model version id was not found in the alternate connection.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """
        new_project_name = new_project_name if new_project_name else f"{self.name} - Copy"
        description = new_description if new_description else f"Copied from {self.name} {self.description}"

        if alternate_workspace:
            if not model_version_id:
                source_model = self.get_model()
                dest_model = alternate_workspace.get_model(source_model.model_name, source_model.version_name)
                model_version_id = dest_model.id
            project = alternate_workspace.create_project(
                new_project_name,
                description,
                model_version_id,
                default_pool_name=default_pool_name,
                default_pool_id=default_pool_id,
            )
            project.copy_project_from_project(
                self, folder_path, resolve_file_callback
            )  # post input data ensures the runs are processed
        else:
            project = self.workspace.create_project(
                new_project_name,
                description,
                model_version_id=model_version_id if model_version_id else self.model_version_id,
                source_project_id=self.id,
                default_pool_name=default_pool_name,
                default_pool_id=default_pool_id,
            )
            _ensure_runs_are_processed(project.get_runs(), self.connection._run_processing_minutes)

        return project

    def copy_project_from_project(
        self,
        project_to_copy_from: "Project",
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> None:
        """Copies data from another project.

        Args:
            project_to_copy_from: The project that will be copied.
            folder_path: Optional folder path to upload files from. Defaults to None. Note that files in the
                alternate workspace take priority over files in the folder_path.
            resolve_file_callback: Optional function for handling file references during cross-workspace copying.
                Accepts (original_file, existing_file, folder_path, workspace, logger) and returns the file name to use.
                Default resolution policy: check if file already exists in alternate workspace, then try uploading from
                folder_path if provided, otherwise leave reference blank and log a warning.

        Raises:
            ProjectNamingError: Copied projects require a different name or environment from the original.
            RunNotFoundError: Project has no runs or starting run not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
            RunStateTimeOutError: Runs are still processing after reaching the total wait time limit.
        """

        if project_to_copy_from.web_app_url == self.web_app_url:
            raise _log_and_get_exception(
                ProjectNamingError,
                "Copied projects require a different name or environment from the original.",
            )

        self._find_and_copy_runs_recursive(
            project_to_copy_from.get_base_run(), project_to_copy_from, None, folder_path, resolve_file_callback
        )

    def create_run(
        self,
        run_name: str,
        parent_id: int,
        description: str = "",
        make_name_unique: bool = False,
        auto_delete_minutes: Optional[int] = None,
    ) -> "Run":
        """Creates a new Run in the project.

        Args:
            run_name: The name given to the new run. Maximum of 100 characters and must be unique across all other runs
                in this project.
            parent_id: The id value for the run that you want to set as the parent of this new run.
            description: Description of the run. Defaults to "".
            make_name_unique: If supplied, indicates that the system should automatically append a unique identifier to
                the run name to ensure it is unique. Defaults to False.
            auto_delete_minutes: If supplied, indicates that we wish the system to automatically delete the run and all
                its data after the specified time in minutes has elapsed. Defaults to None.

        Returns:
            The newly created run.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        run_to_create = CreateRun(
            name=run_name,
            parent_id=parent_id,
            description=description,
            make_name_unique=make_name_unique,
        )

        if auto_delete_minutes:
            run_to_create.auto_delete_minutes = auto_delete_minutes

        response = create_run_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            client=self.connection._get_authenticated_client(),
            body=run_to_create,
        )
        raw_run: ClientRun = self._validate_response(response, RunResponse, ClientRun)
        logger.info(f"Run created - {raw_run.name}")

        return Run(self, raw_run.to_dict())

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_pool_name: Optional[str] = None,
        default_pool_id: Optional[int] = None,
    ) -> None:
        """Updates the project properties.

        Args:
            name: New name for the project. Maximum of 100 characters and must be unique. Optional.
            description: New description for the project. Optional.
            default_pool_name: New default pool name for the project. Optional.
            default_pool_id: New default pool id for the project. Can be used instead of default_pool_name. Optional.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        update_project_model = UpdateProject()
        if name:
            update_project_model.name = name
        if description is not None:
            update_project_model.description = description

        if default_pool_name and default_pool_id:
            _log_and_get_exception(ProjectParameterError, "Cannot provide both default_pool_name and default_pool_id")
        elif default_pool_name:
            update_project_model.default_pool = default_pool_name
        elif default_pool_id:
            update_project_model.default_pool_id = default_pool_id

        response = update_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            client=self.connection._get_authenticated_client(),
            body=update_project_model,
        )

        raw_project_response: ClientProject = _ResponseValidator._validate_response(
            response, ProjectResponse, ClientProject
        )
        project_response: Project = Project(self.workspace, raw_project_response.to_dict())
        # Least surprise if I update the current project object after a successful update.
        self.name = project_response.name
        self.description = project_response.description
        self.default_pool_name = project_response.default_pool_name
        self.default_pool_id = project_response.default_pool_id

        log_message = "Project updated."
        if name:
            log_message += f" New name: {self.name}, expected new name: {name}."
        if description is not None:
            log_message += f" New description: {self.description}, expected new description: {description}."
        if default_pool_name or default_pool_id:
            log_message += (
                f" New default pool name: {self.default_pool_name}, expected new pool name: {default_pool_name}."
            )
            log_message += f" New default pool id: {self.default_pool_id}, expected new pool id: {default_pool_id}."

        logger.info(log_message)

    def delete(self) -> None:
        """Deletes the project from Igloo Cloud.

        Note:
            This operation is irreversible and will delete all the runs in the project along with all the data stored
            in those runs.

        Raises:
            ProjectDeletionError: Project deletion failed.
            UnsuccessfulRequestError: API response was not successful.
        """
        if self.contains_finalized_runs:
            raise ProjectDeletionError("Cannot delete project with finalized runs.")

        response = delete_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        self._check_response_is_valid(response)
        logger.info(f"Project {self.name} successfully deleted.")

    def get_data_group_names(self) -> list[str]:
        """Retrieves the data group names in the projects first run.

        Returns:
            List of data group names.

        Raises:
            ProjectHasNoRunsError: Project has no runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if self.get_runs() == []:
            raise _log_and_get_exception(ProjectHasNoRunsError, "Can not get data groups as no runs in project.")

        run = self.get_runs()[0]
        data_groups = run.get_data_groups()
        return [item["name"] for item in data_groups]

    def get_data_group_name_for_table(self, data_table_name: str) -> str:
        """Retrieves the name of the data group to which a given data table belongs.

        Args:
            data_table_name: Name of the data table.

        Returns:
            Data group name.

        Raises:
            DataTableNotFoundError: Data table not found.
            ProjectHasNoRunsError: Project has no runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        for data_group_name in self.get_data_group_names():
            if data_group_name in self._tables.keys():
                if data_table_name in [t["name"] for t in self._tables[data_group_name]]:
                    return data_group_name
            else:
                if data_table_name in [t["name"] for t in self.get_data_tables_in_data_group(data_group_name)]:
                    return data_group_name

        raise _log_and_get_exception(DataTableNotFoundError, f"data table {data_table_name} not found.")

    def get_data_tables_in_data_group(self, data_group_name: str) -> list[dict]:
        """Retrieves all data tables in a data group.

        Args:
            data_group_name: Data group name.

        Returns:
            A list of data groups, where each data group is represented as a dictionary.

        Raises:
            ProjectHasNoRunsError: There are no runs in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        run = self.get_base_run()

        if data_group_name in self._tables.keys():
            return cast(list[dict], self._tables[data_group_name])

        response = list_data_tables_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            run_id=run.id,
            data_group_name=data_group_name,
            client=self.connection._get_authenticated_client(),
        )
        raw_data_tables: list[DataTableNode] = self._validate_response(
            response, DataTableNodeArrayResponse, DataTableNode
        )
        logger.info(f"Data tables in data group {data_group_name} retrieved.")

        def recursive_table_extractor(items):
            output = []
            for item in items:
                if item.kind == "Folder":
                    output += recursive_table_extractor(item.children)
                else:
                    output += [item.to_dict()]
            return output

        self._tables = {data_group_name: recursive_table_extractor(raw_data_tables)}

        return cast(list[dict], self._tables[data_group_name])

    def get_data_table_documentation(self, data_table_name: str, data_group_name: str | None = None) -> str | None:
        """Retrieves the markdown documentation for a data table.

        Args:
            data_table_name (str): Name of the data table to fetch documentation for.
            data_group_name (str): Optional. Name of the data group containing the data table to fetch
                documentation for. Defaults to None.


        Returns:
            A string containing the documentation for the data table in markdown format. Returns None if no
                help page exists.
        """
        raw_table = self._get_client_data_table(data_table_name, data_group_name)

        if not raw_table.help_:
            return None

        return self._documentation_fetcher.fetch_documentation(raw_table.help_)

    def get_data_table_metadata(self, data_table_name: str, data_group_name: str | None = None) -> TableDefinition:
        """Retrieves the metadata for a data table including table type, values, and dimensions.

        Args:
            data_table_name: Name of the data table to fetch metadata for.
            data_group_name: Name of the data group containing the data table. Defaults to None.

        Returns:
            A TableDefinition object containing the table's metadata.

        Raises:
            DataTableNotFoundError: Data table not found in the project.
            ProjectHasNoRunsError: Project has no runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        raw_table = self._get_client_data_table(data_table_name, data_group_name)

        return TableDefinition._from_dict(raw_table.to_dict())

    def get_run_result_table_documentation(self, table_name: str, result_name: str) -> str | None:
        """Retrieves the markdown documentation for a run result table.

        Args:
            table_name: Name of the result table to fetch documentation for.
            result_name: Name of the run result containing the table.

        Returns:
            A string containing the documentation for the run result table in markdown format. Returns None if no
                help page exists.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        raw_table = self._get_client_run_result_table(table_name, result_name)

        if not raw_table.help_:
            return None

        return self._documentation_fetcher.fetch_documentation(raw_table.help_)

    def get_run_result_table_metadata(self, table_name: str, result_name: str) -> TableDefinition:
        """Retrieves the metadata for a run result table including table type, values, and dimensions.

        Args:
            table_name: Name of the result table to fetch metadata for.
            result_name: Name of the run result containing the table.

        Returns:
            A TableDefinition object containing the table's metadata.

        Raises:
            ProjectHasNoRunsError: Project has no runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        raw_table = self._get_client_run_result_table(table_name, result_name)

        return TableDefinition._from_dict(raw_table.to_dict())

    def get_model(self) -> "Model":
        """Retrieves the model used by the project.

        Returns:
            Model used by the project.

        Raises:
            ModelNotFoundError: The model version id was not found in the connection.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        for model in self.workspace.get_models():
            if model.id == self.model_version_id:
                return model
        raise _log_and_get_exception(ModelNotFoundError, f"Model {model} not found.")

    def get_runs(self) -> list["Run"]:
        """Retrieves all runs in the project.

        Returns:
            List of all runs found in the project.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_runs_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        raw_runs: list[ClientRun] = self._validate_response(response, RunArrayResponse, ClientRun)
        return [Run(self, run.to_dict()) for run in raw_runs]

    def get_run_by_id(self, run_id: int) -> "Run":
        """Returns a run by ID.

        Args:
            run_id: ID of the run to retrieve.

        Returns:
            Run with the given ID.

        Raises:
            RunNotFoundError: A run with the given ID was not found in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_run_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            run_id=run_id,
            client=self.connection._get_authenticated_client(),
        )
        if response.status_code == 404:
            raise _log_and_get_exception(RunNotFoundError, f"Run with ID {run_id} not found.")
        raw_run: "ClientRun" = self._validate_response(response, RunResponse, ClientRun)
        return Run(self, raw_run.to_dict())

    def get_run(self, run_name: str) -> "Run":
        """Returns a run by name.

        Args:
            run_name: Name of the run to retrieve.

        Returns:
            Run with the given name.

        Raises:
            RunNotFoundError: A run with the given name was not found in the project.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        runs = self.get_runs()
        for run in runs:
            if _casefold_equals(run.name, run_name):
                return run
        raise _log_and_get_exception(RunNotFoundError, f"Run {run_name} not found.")

    def get_base_run(self) -> "Run":
        """Fetches the project run with no parent, i.e. the base run.

        Returns:
            The project's base run.

        Raises:
            RunNotFoundError: Project has no base run.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if self._base_run:
            return self._base_run
        for run in self.get_runs():
            if run.parent_id is None:
                self._base_run = run
                return run
        raise _log_and_get_exception(RunNotFoundError, "Project has no starting run.")

    def output_all_runs(
        self,
        output_folder: str = "output",
        compare_to_folder: str = "",
        compare_tolerance: int = 0,
        pool_name: str | Unset = UNSET,
        pool_id: int | Unset = UNSET,
        wait_seconds: int = 0,
    ) -> Optional[dict[str, list]]:
        """Writes the output tables of all runs to a given folder.

        Optionally you can compare these outputs to another folder of outputs.
        If comparing, differences are written to the compare_to_folder as csvs. This includes a summary of
        differences that are also returned.

        Warning:
            If the run has not been calculated, this will cause the run to be calculated on the specified pool.
            To retrieve results for a specific run without causing a calculation,
            use :py:func:`wtwco.extensions.run.run_result_table_to_csv`.

        Args:
            output_folder: Location to write the output tables. Defaults to "output".
            compare_to_folder: Folder containing another set of output tables for comparison. Defaults to "".
            compare_tolerance: Value that defines a difference. I.e only differences greater than this value will be
                counted. Defaults to 0.
            pool_name: Name of the pool to use for calculating. Defaults to UNSET. If no pool name is given the default
                pool for the project will be used, otherwise the first pool in the workspace will be used.
            pool_id: Id of the pool to use for calculating. Defaults to UNSET. Can be used instead of pool_name.
            wait_seconds: The number of seconds to wait for the run to complete. Defaults to 0.

        Returns:
            Summary of all differences if compare_to_folder is specified else None.
        """
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        super_summary: list[list[Union[str, float, int]]] = [
            ["run name", "output", "total abs difference", "unmatched rows"]
        ]
        run_summary: Optional[dict[str, list]] = {} if compare_to_folder != "" else None
        for run in self.get_runs():
            folder_path = os.path.join(output_folder, run.name)
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            run.output_tables_to_folder(folder_path, pool_name, pool_id, wait_seconds)

            # Optionally compares to other folder of runs. (Currently) assumes all runs are present.
            if compare_to_folder != "" and run_summary is not None:
                folder_path2 = os.path.join(compare_to_folder, run.name)

                testing_folder_path = os.path.join(output_folder, "test_output")
                if not os.path.exists(testing_folder_path):
                    os.mkdir(testing_folder_path)
                testing_folder_path = os.path.join(testing_folder_path, run.name)
                if not os.path.exists(testing_folder_path):
                    os.mkdir(testing_folder_path)

                summary = run.compare_output_csvs_in_folder(
                    folder_path2, folder_path, compare_tolerance, testing_folder_path
                )
                run_summary[run.name] = [row[0] for row in summary[1:] if row[1] != 0 or row[2] != 0]
                updated_summary: list[list[Union[str, float, int]]] = [[run.name, *s] for s in summary[1:]]
                super_summary.extend(updated_summary)

        if compare_to_folder != "":
            summary_file = os.path.join(output_folder, "test_output", "summary.csv")
            with open(summary_file, "w", newline="") as file:
                csvwriter = csv.writer(file)
                csvwriter.writerows(super_summary)

        return run_summary

    def odata_get_data_table(self, table_name: str, **kwargs) -> list[dict[str, Any]]:
        """Returns the data table with table_name for all runs within a project.

        Args:
            table_name: Full name of table to get data from.
            **kwargs: for OData operations `filter_`, `select`, `orderby`, `top`, `skip` and `count`.

        Returns:
            A list of dictionaries where each dictionary is a row of data within the table and includes the version id
            for that row. For example:

            ``[{'Version': '585r1', 'UDSimple': 'User 1', 'Value': 2.0},
            {'Version': '585r2', 'UDSimple': 'User 1', 'Value': 0.25},
            {'Version': '586r1', 'UDSimple': 'User 1', 'Value': 0.75}]``

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = get_o_data_for_project.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            table_name=table_name,
            client=self.connection._get_authenticated_client(),
            **kwargs,
        )
        self._check_response_is_valid(response)
        values = cast(
            list[GetODataForProjectResponse200ValueItem], cast(GetODataForProjectResponse200, response.parsed).value
        )

        return [value.additional_properties for value in values]

    def _get_client_run_result_table(self, table_name: str, result_name: str):
        base_run = self.get_base_run()
        response = get_result_table_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            run_id=base_run.id,
            run_result_name=result_name,
            result_table_name=table_name,
            client=self.connection._get_authenticated_client(),
            include=DataTableInclude.DEFINITION,
        )
        raw_table: ClientTableData = self._validate_response(response, TableDataResponse, ClientTableData)
        return raw_table

    def _get_client_data_table(self, data_table_name: str, data_group_name: str | None = None) -> ClientTableData:
        if not data_group_name:
            data_group_name = self.get_data_group_name_for_table(data_table_name)

        base_run = self.get_base_run()
        response = get_data_table_for_run.sync_detailed(
            workspace_id=self.workspace.id,
            project_id=self.id,
            run_id=base_run.id,
            data_group_name=data_group_name,
            data_table_name=data_table_name,
            client=self.connection._get_authenticated_client(),
            include=DataTableInclude.DEFINITION,
        )
        raw_table: ClientTableData = self._validate_response(response, TableDataResponse, ClientTableData)
        return raw_table

    @property
    def _tables(self) -> dict[str, dict]:
        return self.__tables

    @_tables.setter
    def _tables(self, value: dict) -> None:
        """Note only adds to the already existing dictionary. Also is not called with the key."""
        for key, item in value.items():
            self.__tables[key] = item

    def _find_and_copy_runs_recursive(
        self,
        run_to_copy: "Run",
        project_to_copy_from: "Project",
        copied_run_parent_id: Optional[int] = None,
        folder_path: Optional[str] = None,
        resolve_file_callback: Optional["FileReferenceCopyPolicy"] = None,
    ) -> None:
        copy_of_run = run_to_copy.copy_run(
            project=self,
            parent_id=copied_run_parent_id,
            only_copy_owned_datagroups=True,
            folder_path=folder_path,
            resolve_file_callback=resolve_file_callback,
        )

        child_runs = [r for r in project_to_copy_from.get_runs() if r.parent_id == run_to_copy.id]
        for child_run in child_runs:
            self._find_and_copy_runs_recursive(
                child_run, project_to_copy_from, copy_of_run.id, folder_path, resolve_file_callback
            )

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global Run
        from wtwco_igloo import Run
