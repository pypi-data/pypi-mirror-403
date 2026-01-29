from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from wtwco_igloo import Connection, Run, RunResultTableNode


class RunResult(object):
    """
    A class to represent the result of a run.

    Attributes:
        name (str): Name of the run result.
        display_name (str): User visible name of the run result.
        is_in_use (bool): True if the run result is in use, false otherwise.
        run (Run): The run object that this result belongs to.
        connection (Connection): Connection object used to authenticate with Igloo Cloud.
    """

    def __init__(self, run: "Run", run_result_dict: dict) -> None:
        self.name: str = run_result_dict["name"]
        self.display_name: str = run_result_dict["displayName"]
        self.is_in_use: bool = run_result_dict["isInUse"]
        self.run: Run = run
        self.connection: Connection = run.connection
        self._import_classes()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RunResult):
            return NotImplemented
        return (
            self.name == other.name
            and self.display_name == other.display_name
            and self.is_in_use == other.is_in_use
            and self.run.id == other.run.id
        )

    def __str__(self) -> str:
        return f"name: {self.name}"

    def get_table_nodes(self) -> list["RunResultTableNode"]:
        """Retrieves the top level of result table nodes for this run result.

        Returns:
            A list containing the top level of result table nodes for this run result. Each node may be a table or a
            folder containing tables or other folders.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return self.run.get_run_result_table_nodes(self.name)

    def get_tables(self) -> list["RunResultTableNode"]:
        """Retrieves all result tables (tables only, not folders) for this run result.

        Returns:
            A list containing all of the table nodes in the run result that are not folders. This
                includes those within folders.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """

        def recursive_table_extractor(items: list["RunResultTableNode"]) -> Generator["RunResultTableNode", None, None]:
            for item in items:
                if item.folder:
                    yield from recursive_table_extractor(item.children)
                else:
                    yield item

        return list(recursive_table_extractor(self.get_table_nodes()))

    def get_table_data(self, table_name: str) -> dict:
        """Retrieves result data for a given table, only if the run has been calculated.

        Note:
            This method does not cause the run to be calculated. It is used to retrieve results for a specific run
            without causing a calculation.

        Args:
            table_name: Name of the result data table.

        Returns:
            A dictionary containing the requested result data table along with its metadata.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        return self.run.get_run_result_table_data(table_name, self.name)

    @staticmethod
    def _import_classes() -> None:
        """Import classes to avoid circular imports."""
        global Run
        from wtwco_igloo import Run
