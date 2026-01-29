from asyncio import AbstractEventLoop
from typing import TYPE_CHECKING, Optional, Union, cast
from urllib.parse import urljoin

from wtwco_igloo.api_client.api.calculation_pools import list_calculation_pools_for_workspace
from wtwco_igloo.api_client.api.models import list_models_for_workspace
from wtwco_igloo.api_client.api.projects import create_project, fetch_project, list_projects
from wtwco_igloo.api_client.api.uploaded_files import fetch_uploaded_file, list_uploaded_files
from wtwco_igloo.api_client.api.workspaces import delete_workspace
from wtwco_igloo.api_client.models import (
    CalculationPool as ClientCalculationPool,
)
from wtwco_igloo.api_client.models import (
    CalculationPoolArrayResponse,
    CreateProject,
    ModelArrayResponse,
    ModelVersion,
    ProjectArrayResponse,
    ProjectResponse,
    UploadedFileArrayResponse,
    UploadedFileResponse,
)
from wtwco_igloo.api_client.models import Model as ClientModel
from wtwco_igloo.api_client.models import (
    Project as ClientProject,
)
from wtwco_igloo.api_client.models import (
    UploadedFile as ClientUploadedFile,
)
from wtwco_igloo.extensions.utils.errors.model_errors import ModelNotFoundError
from wtwco_igloo.extensions.utils.errors.project_errors import ProjectNotFoundError, ProjectParameterError
from wtwco_igloo.extensions.utils.errors.uploaded_file_errors import UploadedFileNotFoundError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception
from wtwco_igloo.extensions.utils.helpers import _casefold_equals
from wtwco_igloo.extensions.utils.uploader import _Uploader
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator
from wtwco_igloo.logger import logger

if TYPE_CHECKING:
    from wtwco_igloo import CalculationPool, Connection, Model, Project, UploadedFile


class Workspace(object):
    """Represents a workspace in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the workspace.
        name (str): Name of the workspace.
        description (str): Description of the workspace.
        connection (Connection): Connection object used to authenticate with Igloo Cloud.
        web_app_url (str): URL to the Igloo Cloud project.
    """

    def __init__(
        self, connection: "Connection", workspace_dict: dict, event_loop: Optional[AbstractEventLoop] = None
    ) -> None:
        self.id: int = workspace_dict["id"]
        self.name: str = workspace_dict["name"]
        self.description: str = workspace_dict["description"]
        self.connection: Connection = connection
        self.web_app_url: str = urljoin(connection.web_app_url, f"workspaces/{self.id}/")
        self._import_classes()
        self._validate_response = _ResponseValidator._validate_response
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid
        self._uploader = _Uploader(self.id, connection, event_loop)

    def __enter__(self) -> "Workspace":
        self._uploader.__enter__()
        return self

    def __exit__(self) -> None:
        self._uploader.__exit__()

    def __str__(self) -> str:
        return f"id: {self.id}, name: {self.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return NotImplemented
        return self.id == other.id and self.name == other.name and self.description == other.description

    def delete(self) -> None:
        """Deletes the workspace from Igloo Cloud. This will only succeed if the workspace has no projects.

        Note:
            This operation is irreversible.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = delete_workspace.sync_detailed(
            workspace_id=self.id,
            client=self.connection._get_authenticated_client(),
        )
        self._check_response_is_valid(response)
        logger.info(f"Workspace {self.name} successfully deleted.")

    def get_calculation_pools(self) -> list["CalculationPool"]:
        """Retrieves the list of calculation pools assigned to this workspace.

        Returns:
            List of calculation pools.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_calculation_pools_for_workspace.sync_detailed(
            workspace_id=self.id, client=self.connection._get_authenticated_client()
        )
        calculation_pools: list[ClientCalculationPool] = self._validate_response(
            response, CalculationPoolArrayResponse, ClientCalculationPool
        )
        return [CalculationPool.from_dict(pool.to_dict()) for pool in calculation_pools]

    def get_models(self) -> list["Model"]:
        """Retrieves the list of models assigned to this workspace.

        Returns:
            List of available models.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_models_for_workspace.sync_detailed(
            workspace_id=self.id, client=self.connection._get_authenticated_client()
        )
        raw_models: list[ClientModel] = self._validate_response(response, ModelArrayResponse, ClientModel)
        return [
            Model(
                {
                    "model_name": raw_model.name,
                    "version_name": version.name,
                    "semantic_version": version.sem_version,
                    "type": version.type_,
                    "description": version.description,
                    "id": version.id,
                    "uploaded_by": version.uploaded_by or None,
                    "upload_time": version.upload_time or None,
                },
            )
            for raw_model in raw_models
            for version in cast(list[ModelVersion], raw_model.versions)
        ]

    def get_model(self, model_name: str, version_name: str) -> "Model":
        """Retrieves model with the given name and version.

        Args:
            model_name: Name of model to return.
            version_name: Version name of the model to return.

        Returns:
            The requested model.

        Raises:
            ModelNotFoundError: Requested model was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        for model in self.get_models():
            if _casefold_equals(model.model_name, model_name) and _casefold_equals(model.version_name, version_name):
                return model
        raise _log_and_get_exception(ModelNotFoundError, f"Model '{model_name}/{version_name}' not found.")

    def get_uploaded_files(self) -> list["UploadedFile"]:
        """Retrieves the list of uploaded files available within the workspace.

        Returns:
            List of available uploaded files.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_uploaded_files.sync_detailed(
            workspace_id=self.id, client=self.connection._get_authenticated_client()
        )
        raw_uploaded_files: list[ClientUploadedFile] = self._validate_response(
            response, UploadedFileArrayResponse, ClientUploadedFile
        )

        return [UploadedFile(uploaded_file.to_dict(), self.connection) for uploaded_file in raw_uploaded_files]

    def get_uploaded_file_by_id(self, uploaded_file_id: int) -> "UploadedFile":
        """Fetches the uploaded file details from Igloo Cloud by its ID.

        Args:
            uploaded_file_id: The ID of the uploaded file.

        Returns:
            The details of the uploaded file.

        Raises:
            UploadedFileNotFoundError: An uploaded file with the given ID was not found in the workspace.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = fetch_uploaded_file.sync_detailed(
            workspace_id=self.id,
            file_id=uploaded_file_id,
            client=self.connection._get_authenticated_client(),
        )
        if response.status_code == 404:
            raise _log_and_get_exception(
                UploadedFileNotFoundError, f"Uploaded file with ID {uploaded_file_id} not found."
            )
        raw_file: "ClientUploadedFile" = self._validate_response(response, UploadedFileResponse, ClientUploadedFile)
        return UploadedFile(raw_file.to_dict(), self.connection)

    def get_uploaded_file(self, uploaded_file_name: str) -> "UploadedFile":
        """Fetches the uploaded file details from Igloo Cloud by its name.

        Args:
            uploaded_file_name: The name of the uploaded file.

        Returns:
            The details of the uploaded file.

        Raises:
            UploadedFileNotFoundError: An uploaded file with the given name was not found in the workspace.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        uploaded_files = self.get_uploaded_files()
        for uploaded_file in uploaded_files:
            if _casefold_equals(uploaded_file.name, uploaded_file_name):
                return uploaded_file
        raise _log_and_get_exception(
            UploadedFileNotFoundError, f"Uploaded file with name {uploaded_file_name} not found."
        )

    def create_uploaded_file(
        self, file_path: str, uploaded_file_name: str = "", description: str = ""
    ) -> "UploadedFile":
        """Creates a new uploaded file using the contents of the file specified by file_path.

        Args:
            file_path: Path to the file to upload.
            uploaded_file_name: Name of the uploaded file to create. Maximum of 100 characters and must be unique.
                Defaults to using an auto-generated name that is guaranteed to be unique based on the name of the file
                specified by file_path.
            description: A description of the uploaded file. Defaults to "".

        Returns:
            Uploaded file.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        uploaded_file_dict: dict[str, UploadedFile] = self.upload_files((file_path, description))
        uploaded_file = next(iter(uploaded_file_dict.values()))
        if uploaded_file_name != "" and uploaded_file.name != uploaded_file_name:
            uploaded_file.edit_name_or_description(name=uploaded_file_name)
        return uploaded_file

    def get_projects(self) -> list["Project"]:
        """Retrieves the list of projects available within the workspace.

        Returns:
            List of available projects.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_projects.sync_detailed(workspace_id=self.id, client=self.connection._get_authenticated_client())
        raw_projects: list[ClientProject] = self._validate_response(response, ProjectArrayResponse, ClientProject)
        return [Project(self, proj.to_dict()) for proj in raw_projects]

    def get_project_by_id(self, project_id: int) -> "Project":
        """Retrieves a project by ID.

        Args:
            project_id: ID of the project to retrieve.

        Returns:
            Project with the given ID.

        Raises:
            ProjectNotFoundError: Project with the given ID was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = fetch_project.sync_detailed(
            workspace_id=self.id, project_id=project_id, client=self.connection._get_authenticated_client()
        )
        if response.status_code == 404:
            raise _log_and_get_exception(ProjectNotFoundError, f"Project with ID {project_id} not found.")

        self._check_response_is_valid(response)
        raw_project: "ClientProject" = self._validate_response(response, ProjectResponse, ClientProject)
        return Project(self, raw_project.to_dict())

    def get_project(self, project_name: str) -> "Project":
        """Retrieves a project by name.

        Args:
            project_name: Name of the project to retrieve.

        Returns:
            Project with the given name.

        Raises:
            ProjectNotFoundError: Project with the given name was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        projects = self.get_projects()
        for project in projects:
            if _casefold_equals(project.name, project_name):
                return project
        raise _log_and_get_exception(ProjectNotFoundError, f"Project {project_name} not found.")

    def get_or_create_project(
        self,
        project_name: str,
        model_name: str,
        version_name: str,
        default_pool_name: Optional[str] = None,
        description: str = "",
    ) -> "Project":
        """Gets the named project in this workspace for the model. Creating the project if necessary.

        Args:
            project_name: Name of the project, if it does not exist it will be created. Maximum of 100 characters and must be unique.
            model_name: Name of the model.
            version_name: Version of the model.
            default_pool_name: Name of the default calculation pool to use for the project. Defaults to None.
            description: Description of the project, if the project exists this be ignored. Defaults to "".

        Returns:
            Existing or newly created project. If the project exists but is not associated with the model,
            an error is raised. If the project exists and the default pool is not set, it will be set to the
            default_pool_name.

        Raises:
            ProjectNotFoundError: Project with the given name was found but not associated with the model.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """

        # Let model failure raise an error
        model = self.get_model(model_name, version_name)

        # Get or create the project
        try:
            project = self.get_project(project_name)
        except ProjectNotFoundError:
            project = self.create_project(project_name, description, model.id, default_pool_name=default_pool_name)

        # Confirm that the project is associated with the model
        if project.model_version_id != model.id:
            raise _log_and_get_exception(
                ProjectNotFoundError,
                f"Project {project_name} is not associated with model {model_name} version {version_name}.",
            )

        # If the project default pool is not set, set it to the default pool of the model if we are given one
        if not project.default_pool_name and default_pool_name:
            project.update(default_pool_name=default_pool_name)

        return project

    def create_project(
        self,
        project_name: str,
        description: str = "",
        model_version_id: int = 0,
        source_run_id: Optional[int] = None,
        source_project_id: Optional[int] = None,
        default_pool_name: Optional[str] = None,
        default_pool_id: Optional[int] = None,
    ) -> "Project":
        """Creates a new project.

        Args:
            project_name: Name of the project to create. Maximum of 100 characters and must be unique.
            description: A description of the project. Defaults to "".
            model_version_id: Id of model to use in this project. Defaults to 0. Note that it's not possible to change
                the model associated with a project after creation.
            source_run_id: Id of run to initialise the first run of the new project. Defaults to None. The source run
                must associated with a compatible model. Compatible meaning it the models share the same name. Models
                with the same name but different versions are also compatible.
            source_project_id: Id of project to copy. As with the source run a source project must be associated with a
                compatible model. Defaults to None.
            default_pool_name: Name of the default calculation pool to use for the project. Defaults to None.
            default_pool_id: Id of the default calculation pool to use for the project. Defaults to None. Can be used
                instead of default_pool_name.

        Returns:
            Newly created project.

        Raises:
            ProjectParameterError: source_run_id and source_project_id are both set.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if source_project_id and source_run_id:
            raise _log_and_get_exception(ProjectParameterError, "Cannot set both source_run_id and source_project_id.")
        if default_pool_name and default_pool_id:
            raise _log_and_get_exception(ProjectParameterError, "Cannot set both default_pool_name and default_pool_id")

        project_to_create = CreateProject(name=project_name, description=description, model_version_id=model_version_id)
        if source_run_id:
            project_to_create.source_run_id = source_run_id
        if source_project_id:
            project_to_create.source_project_id = source_project_id

        if default_pool_name:
            project_to_create.default_pool = default_pool_name
        elif default_pool_id:
            project_to_create.default_pool_id = default_pool_id

        response = create_project.sync_detailed(
            workspace_id=self.id, client=self.connection._get_authenticated_client(), body=project_to_create
        )
        raw_project: ClientProject = self._validate_response(response, ProjectResponse, ClientProject)
        logger.info(f"Project {project_name} was successfully created.")

        return Project(self, raw_project.to_dict())

    def upload_folder(self, folder_path: str, folder_description: str = "") -> dict[str, "UploadedFile"]:
        """Uploads all csv files in a folder to Igloo Cloud. Returns a dictionary of file names to uploaded file
        instances.

        Args:
            folder_path: Path to directory containing csv files to upload.
            folder_description: Describes the files in the folder. Defaults to "". Note the description is applied to
                each file within the folder.

        Returns:
            Map of uploaded file names to the corresponding uploaded file in Igloo Cloud.

        Raises:
            FolderNotFoundError: Given folder path is not an existing directory.
            FileNotFoundError: No files were found in the folder.
            NonCsvFileError: Only csv files are accepted.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return self._uploader._upload_folder(folder_path, folder_description=folder_description)

    def upload_files(self, *files_and_descriptions: Union[str, tuple[str, str]]) -> dict[str, "UploadedFile"]:
        """Uploads files to Igloo Cloud. Returns a dictionary of file names to uploaded file instances.

        If multiple files with the same base names are uploaded, the shared folder will be the common path of all files.

        Args:
            files_and_descriptions: Files to upload to Igloo Cloud and related
                descriptions. Descriptions default to empty strings if they are not provided.

        Returns:
            Map of uploaded file names to the corresponding uploaded file in Igloo Cloud.

        Raises:
            FileNotFoundError: One or more of the files were not found.
            NonCsvFileError: Only csv files are accepted.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return self._uploader._upload_files(list(files_and_descriptions))

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global CalculationPool, Model, Project, UploadedFile
        from wtwco_igloo import CalculationPool, Model, Project, UploadedFile
