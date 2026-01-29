from typing import TYPE_CHECKING

from wtwco_igloo.extensions.table_definition import TableDefinition
from wtwco_igloo.extensions.utils.documentation_fetcher import _DocumentationFetcher
from wtwco_igloo.extensions.utils.errors.run_errors import InvalidNodeOperationError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception

if TYPE_CHECKING:
    from wtwco_igloo import Connection, Run


class RunResultTableNode(object):
    """A class that represents a table node in a run result.

    Attributes:
        name (str): Name of the run result.
        display_name (str): User visible name of the run result.
        run_result_name (str): The name of the run result this node belongs to.
        folder (bool): True if the node is a folder, false otherwise.
        children (list[RunResultTableNode]): List of child nodes, if this node is a folder.
        run (Run): The run object that this result belongs to.
        connection (Connection): Connection object used to authenticate with Igloo Cloud.
    """

    def __init__(self, run: "Run", run_result_name: str, run_result_dict: dict) -> None:
        self.name: str = run_result_dict["name"]
        self.display_name: str = run_result_dict["displayName"]
        self.run_result_name: str = run_result_name
        self.folder: bool = run_result_dict["kind"] == "Folder"
        self.help_url: str | None = run_result_dict.get("help")
        self.children: list["RunResultTableNode"] = (
            [RunResultTableNode(run, run_result_name, child) for child in run_result_dict["children"]]
            if "children" in run_result_dict
            and isinstance(run_result_dict["children"], list)
            and len(run_result_dict["children"]) > 0
            else []
        )
        self.run: Run = run
        self.connection: Connection = run.connection
        self._documentation_fetcher = _DocumentationFetcher(self.connection)
        self._import_classes()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RunResultTableNode):
            return NotImplemented
        return (
            self.name == other.name
            and self.run_result_name == other.run_result_name
            and self.folder == other.folder
            and self.run.id == other.run.id
        )

    def __str__(self) -> str:
        return f"name: {self.name}"

    def get_table_data(self) -> dict:
        """Retrieves result data this table, only if the run has been calculated.

        Note:
            This method does not cause the run to be calculated. It is used to retrieve results for a specific run
            without causing a calculation.

        Returns:
            A dictionary containing the requested result data table along with its metadata.

        Raises:
            InvalidNodeOperationError: This node is a folder, not a table.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if self.folder:
            raise _log_and_get_exception(
                InvalidNodeOperationError,
                f"Cannot get table data for '{self.name}' because it is a folder, not a table.",
            )
        return self.run.get_run_result_table_data(self.name, self.run_result_name)

    def get_table_documentation(self) -> str | None:
        """Retrieves the markdown documentation for this run result table or folder.

        Returns:
            A string containing the documentation for the table or folder in markdown format. Returns None if no
                help page exists.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if not self.folder:
            return self.run.project.get_run_result_table_documentation(self.name, self.run_result_name)
        if self.help_url:
            return self._documentation_fetcher.fetch_documentation(self.help_url)

        return None

    def get_table_metadata(self) -> TableDefinition:
        """Retrieves the metadata for this run result table including table type, values, and dimensions.

        Returns:
            A TableDefinition object containing the table's metadata.

        Raises:
            InvalidNodeOperationError: This node is a folder, not a table.
            ProjectHasNoRunsError: Project has no runs.
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        if self.folder:
            raise _log_and_get_exception(
                InvalidNodeOperationError,
                f"Cannot get table metadata for '{self.name}' because it is a folder, not a table.",
            )
        return self.run.project.get_run_result_table_metadata(self.name, self.run_result_name)

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global Run
        from wtwco_igloo import Run
