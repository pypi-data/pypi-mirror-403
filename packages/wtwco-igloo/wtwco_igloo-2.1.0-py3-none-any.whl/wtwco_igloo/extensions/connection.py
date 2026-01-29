from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional, Union
from urllib.parse import quote

from wtwco_igloo.api_client import AuthenticatedClient
from wtwco_igloo.api_client.api.workspaces import create_workspace, fetch_workspace, list_workspaces
from wtwco_igloo.api_client.models import CreateWorkspace, WorkspaceArrayResponse, WorkspaceResponse
from wtwco_igloo.api_client.models import Workspace as ClientWorkspace
from wtwco_igloo.extensions.utils.authentication.authentication_with_refresh import _AuthenticationManagerWithRefresh
from wtwco_igloo.extensions.utils.authentication.authentication_without_refresh import (
    _AuthenticationManagerWithoutRefresh,
)
from wtwco_igloo.extensions.utils.errors.workspace_errors import WorkspaceNotFoundError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception
from wtwco_igloo.extensions.utils.helpers import _standardise_url
from wtwco_igloo.extensions.utils.retry_settings import RetrySettings
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator

if TYPE_CHECKING:
    from wtwco_igloo import Config, Project, Workspace


class Connection(object):
    """Handles connecting to the WTW Igloo Cloud and initial functionality.

    The connection class is constructed via the class methods `from_device_code`, `from_interactive_token`,
    `from_certificate`, and `from_secret`. These class methods cover the different ways to authenticate to Azure and
    all return a connection instance.

    Attributes:
        web_app_url (str): Igloo Cloud Web App URL.
        post_data_row_batch_size (int): Defines the number of rows to send per request when updating a data table, defaults to 10,000.
        config (Config): Access to environment-level resources including models and calculation pools.
    """

    def __init__(
        self,
        authentication_manager: Union[_AuthenticationManagerWithoutRefresh, _AuthenticationManagerWithRefresh],
        run_processing_minutes: int,
    ) -> None:
        self._import_classes()
        self.web_app_url: str = _standardise_url(authentication_manager._api_url, "/manager/")
        self.post_data_row_batch_size: int = 10000
        self._authentication_manager = authentication_manager
        self._run_processing_minutes = run_processing_minutes
        self._validate_response = _ResponseValidator._validate_response
        self.config = Config(self)

    def __str__(self) -> str:
        return self.web_app_url

    @classmethod
    def from_certificate(
        cls,
        api_url: str,
        client_id: str,
        thumbprint: str,
        certificate_path: str,
        tenant_id: str,
        run_processing_minutes: int = 15,
        refresh_connection: bool = False,
        retry_settings: RetrySettings | None = None,
    ) -> "Connection":
        """Connect to Igloo Cloud using a certificate.

        Args:
            api_url: Igloo Cloud API URL
            client_id: App registration GUID.
            thumbprint: Certificate thumbprint.
            certificate_path: Path to .pem certificate file.
            tenant_id: Tenant GUID.
            run_processing_minutes: Maximum time to wait for runs to process. Defaults to 15 minutes.
            refresh_connection: If True, the connection will automatically refresh. Defaults to False.
            retry_settings: Configuration for retry behavior. If None, default settings will be used.

        Returns:
            An authenticated connection to Igloo Cloud.

        Raises:
            AuthenticationError: Failed to authenticate.
        """
        if retry_settings is None:
            retry_settings = RetrySettings()

        authentication_manager = (
            _AuthenticationManagerWithRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
            if refresh_connection
            else _AuthenticationManagerWithoutRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
        )
        authentication_manager._from_certificate(thumbprint, certificate_path)

        return cls(authentication_manager, run_processing_minutes)

    @classmethod
    def from_device_code(
        cls,
        api_url: str,
        client_id: str,
        tenant_id: str,
        run_processing_minutes: int = 15,
        refresh_connection: bool = False,
        retry_settings: RetrySettings | None = None,
        **kwargs: bool,
    ) -> "Connection":
        """Connect to Igloo Cloud using device code flow.

        After connecting your device will be remembered for future connections.

        Args:
            api_url: Igloo Cloud API URL
            client_id: App registration GUID.
            tenant_id: Tenant GUID.
            run_processing_minutes: Maximum time to wait for runs to process. Defaults to 15 minutes.
            refresh_connection: If True, the connection will automatically refresh. Defaults to False.
            retry_settings: Configuration for retry behavior. If None, default settings will be used.
            **kwargs: Additional keyword arguments used for testing only.

        Returns:
            An authenticated connection to Igloo Cloud.

        Raises:
            AuthenticationError: Failed to authenticate.
        """
        if retry_settings is None:
            retry_settings = RetrySettings()

        authentication_manager = (
            _AuthenticationManagerWithRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
            if refresh_connection
            else _AuthenticationManagerWithoutRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
        )
        authentication_manager._from_device_code(**kwargs)

        return cls(authentication_manager, run_processing_minutes)

    @classmethod
    def from_interactive_token(
        cls,
        api_url: str,
        client_id: str,
        tenant_id: str,
        run_processing_minutes: int = 15,
        refresh_connection: bool = False,
        enable_broker_on_windows: bool = False,
        retry_settings: RetrySettings | None = None,
        **kwargs: bool,
    ) -> "Connection":
        """Connect to Igloo Cloud using interactive token.

        For information on using the Windows Account Manager broker see:
        https://learn.microsoft.com/en-us/entra/msal/python/advanced/wam

        After connecting your device will be remembered for future connections.

        Args:
            api_url: Igloo Cloud API URL
            client_id: App registration GUID.
            tenant_id: Tenant GUID.
            run_processing_minutes: Maximum time to wait for runs to process. Defaults to 15 minutes.
            refresh_connection: If True, the connection will automatically refresh. Defaults to False.
            enable_broker_on_windows: If True, the broker will be enabled on Windows. Defaults to False.
            retry_settings: Configuration for retry behavior. If None, default settings will be used.
            **kwargs: Additional keyword arguments used for testing only.

        Returns:
            An authenticated connection to Igloo Cloud.

        Raises:
            AuthenticationError: Failed to authenticate.
        """
        if retry_settings is None:
            retry_settings = RetrySettings()

        authentication_manager = (
            _AuthenticationManagerWithRefresh(
                api_url,
                client_id,
                tenant_id,
                enable_broker_on_windows,
                retry_settings,
            )
            if refresh_connection
            else _AuthenticationManagerWithoutRefresh(
                api_url,
                client_id,
                tenant_id,
                enable_broker_on_windows,
                retry_settings,
            )
        )
        authentication_manager._from_interactive_token(**kwargs)

        return cls(authentication_manager, run_processing_minutes)

    @classmethod
    def from_secret(
        cls,
        api_url: str,
        client_id: str,
        secret: str,
        tenant_id: str,
        run_processing_minutes: int = 15,
        refresh_connection: bool = False,
        retry_settings: RetrySettings | None = None,
    ) -> "Connection":
        """Connect to Igloo Cloud using a secret.

        Args:
            api_url: Igloo Cloud API URL
            client_id: App registration GUID.
            secret: Secret for authenticating with tenant.
            tenant_id: Tenant GUID.
            run_processing_minutes: Maximum time to wait for runs to process. Defaults to 15 minutes.
            refresh_connection: If True, the connection will automatically refresh. Defaults to False.
            retry_settings: Configuration for retry behavior. If None, default settings will be used.

        Returns:
            An authenticated connection to Igloo Cloud.

        Raises:
            AuthenticationError: Failed to authenticate.
        """
        if retry_settings is None:
            retry_settings = RetrySettings()

        authentication_manager = (
            _AuthenticationManagerWithRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
            if refresh_connection
            else _AuthenticationManagerWithoutRefresh(
                api_url,
                client_id,
                tenant_id,
                False,
                retry_settings,
            )
        )
        authentication_manager._from_secret(secret)

        return cls(authentication_manager, run_processing_minutes)

    def get_workspaces(self) -> list["Workspace"]:
        """Retrieves the list of workspaces available to the API.

        Returns:
            List of available workspaces.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_workspaces.sync_detailed(client=self._get_authenticated_client())
        raw_workspaces: list[ClientWorkspace] = self._validate_response(
            response, WorkspaceArrayResponse, ClientWorkspace
        )
        return [Workspace(self, ws.to_dict()) for ws in raw_workspaces]

    def get_workspace_by_id(self, workspace_id: int) -> "Workspace":
        """Retrieves the workspace with the given ID.

        Args:
            workspace_id: ID of workspace to return.

        Returns:
            Workspace with the given ID.

        Raises:
            WorkspaceNotFoundError: Workspace with the given ID was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = fetch_workspace.sync_detailed(workspace_id, client=self._get_authenticated_client())
        if response.status_code == 404:
            raise _log_and_get_exception(WorkspaceNotFoundError, f"Workspace with ID {workspace_id} not found.")
        raw_workspace: "ClientWorkspace" = self._validate_response(response, WorkspaceResponse, ClientWorkspace)
        return Workspace(self, raw_workspace.to_dict())

    def get_workspace(self, workspace_name: str) -> "Workspace":
        """Retrieves the workspace with the given name.

        Args:
            workspace_name: Name of workspace to return.

        Returns:
            Workspace with the given name.

        Raises:
            WorkspaceNotFoundError: Workspace with the given name was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        workspaces = self.get_workspaces()
        for workspace in workspaces:
            if workspace.name == workspace_name:
                return workspace
        raise _log_and_get_exception(WorkspaceNotFoundError, f"Workspace {workspace_name} not found.")

    def create_workspace(
        self,
        name: str,
        description: str = "",
        suppress_model_assignment: bool = False,
        suppress_calculation_pool_assignment: bool = False,
    ) -> "Workspace":
        """Creates a new Workspace.

        Args:
            name: The name given to the new workspace. Maximum of 100 characters and must be unique across the environment.
            description: Description of the workspace. Defaults to "".
            suppress_model_assignment: If True, model versions will not be automatically assigned to the workspace. Defaults to False.
            suppress_calculation_pool_assignment: If True, calculation pools will not be automatically assigned to the workspace. Defaults to False.

        Returns:
            The newly created workspace.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        workspace_to_create = CreateWorkspace(
            name=name,
            description=description,
            suppress_model_assignment=suppress_model_assignment,
            suppress_calculation_pool_assignment=suppress_calculation_pool_assignment,
        )

        response = create_workspace.sync_detailed(
            client=self._get_authenticated_client(),
            body=workspace_to_create,
        )
        raw_workspace: ClientWorkspace = self._validate_response(response, WorkspaceResponse, ClientWorkspace)
        return Workspace(self, raw_workspace.to_dict())

    def get_or_create_project(
        self,
        workspace_identifier: Union[str, int],
        project_name: str,
        model_name: str,
        version_name: str,
        default_pool_name: Optional[str] = None,
        description: str = "",
    ) -> "Project":
        """Gets the named project from the workspace for the model. Creating the project if necessary.

        Args:
            workspace_identifier: Name or id of an existing workspace.
            project_name: Name of the project, if it does not exist it will be created. Maximum of 100 characters and must be unique.
            model_name: Name of the model.
            version_name: Version of the model.
            default_pool_name: Name of the default calculation pool to use for the project. Defaults to None.
            description: Description of the project, if it exists this be ignored. Defaults to "".

        Returns:
            Existing or newly created project. If the project exists but is not associated with the model,
            an error is raised. If the project exists and the default pool is not set, it will be set to the
            default_pool_name.

        Raises:
            ProjectNotFoundError: Project with the given name was found but not associated with the model.
            WorkspaceNotFoundError: Workspace with the given identifier was not found.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        # Gets the workspace, fails with WorkspaceNotFoundError if it does not exist
        if isinstance(workspace_identifier, int):
            workspace = self.get_workspace_by_id(workspace_identifier)
        else:
            workspace = self.get_workspace(workspace_identifier)

        return workspace.get_or_create_project(
            project_name=project_name,
            description=description,
            model_name=model_name,
            version_name=version_name,
            default_pool_name=default_pool_name,
        )

    def _get_authenticated_client(self) -> AuthenticatedClient:
        return self._authentication_manager._get_authenticated_client()

    @contextmanager
    def attribute_to(self, username: str) -> Iterator[None]:
        """Context manager to temporarily attribute API actions to a given username.

        Args:
            username (str): The username to attribute actions to.

        Yields:
            None: Control is yielded to the with block. No value is produced.
        """

        self._authentication_manager._update_headers(
            {"attributed-to": f"username* = UTF-8''{quote(username, safe='')}"}
        )
        yield
        self._authentication_manager._remove_headers("attributed-to")

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global Model, Project, Workspace, Config
        from wtwco_igloo import Config, Model, Project, Workspace
