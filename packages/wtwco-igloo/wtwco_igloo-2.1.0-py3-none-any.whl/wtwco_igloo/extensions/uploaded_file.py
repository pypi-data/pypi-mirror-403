from typing import TYPE_CHECKING, Union

from wtwco_igloo.api_client.api.uploaded_files import (
    delete_uploaded_file,
    fetch_uploaded_file,
    update_uploaded_file,
)
from wtwco_igloo.api_client.models import UpdateUploadedFile, UploadedFileResponse
from wtwco_igloo.api_client.models import UploadedFile as ClientUploadedFile
from wtwco_igloo.api_client.types import UNSET, Unset
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator
from wtwco_igloo.logger import logger

if TYPE_CHECKING:
    from wtwco_igloo import Connection


class UploadedFile(object):
    """Represents an uploaded file in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the uploaded file.
        workspace_id (int): Identifier value of the workspace.
        name (str): Name of the uploaded file.
        extension (str): The file extension of the uploaded file.
        description (str): The description of the uploaded file.
        upload_status (str): Indicates the upload status of this file. One of UploadNotStarted, Uploading, UploadCompleting, Uploaded or UploadFailedOrCancelled.
        uploaded_by (str): The name of the user who uploaded the content of this file.
        upload_start_time (str): The date and time when the file upload process was initiated.
        size_in_bytes (int): The total size of the file content.
        run_count (int): The number of runs whose input data reference this file.
    """

    def __init__(self, uploaded_file_dict: dict, connection: "Connection") -> None:
        self.id: int = uploaded_file_dict["id"]
        self.workspace_id: int = uploaded_file_dict["workspaceId"]
        self._update_properties_from_dict(uploaded_file_dict)
        self._connection = connection
        self._validate_response = _ResponseValidator._validate_response
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid

    def _update_properties_from_dict(self, uploaded_file_dict: dict) -> None:
        self.name: str = uploaded_file_dict["name"]
        self.extension: str = uploaded_file_dict["extension"]
        self.description: str = uploaded_file_dict["description"]
        self.upload_status: str = uploaded_file_dict["uploadStatus"]
        self.uploaded_by: str = uploaded_file_dict["uploadedBy"]
        self.upload_start_time: str = uploaded_file_dict["uploadStartTime"]
        self.size_in_bytes: int = uploaded_file_dict["sizeInBytes"]
        self.run_count: int = uploaded_file_dict["runCount"]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UploadedFile):
            return NotImplemented
        return self.id == other.id and self.workspace_id == other.workspace_id

    def __str__(self) -> str:
        return f"id: {self.id}, name: {self.name}, extension: {self.extension}, upload_status: {self.upload_status}"

    def edit_name_or_description(self, name: Union[Unset, str] = UNSET, description: Union[Unset, str] = UNSET) -> None:
        """Edits the name or description of the uploaded file.

        Args:
            name: New name for the uploaded file. Leave blank to keep current name. Defaults to UNSET.
            description : New description for the uploaded file. Leave blank to keep current description. Defaults to UNSET.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = update_uploaded_file.sync_detailed(
            workspace_id=self.workspace_id,
            file_id=self.id,
            client=self._connection._get_authenticated_client(),
            body=UpdateUploadedFile(name=name, description=description),
        )
        self._check_response_is_valid(response)
        self.name = self.name if isinstance(name, Unset) else name
        self.description = self.description if isinstance(description, Unset) else description

        logger.info(
            (
                f"{f'Uploaded file name was successfully updated to {name}.' if name is not UNSET else ''}\n"
                f"{f'Uploaded file description was successfully updated to {description}.' if description is not UNSET else ''}"
            )
        )

    def delete(self) -> None:
        """Deletes the uploaded file from Igloo Cloud.

        Note:
            This operation will fail if the file is being referenced by a run in the workspace. This is to avoid
            accidental deletion of files that are still in use.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
        """
        response = delete_uploaded_file.sync_detailed(
            workspace_id=self.workspace_id,
            file_id=self.id,
            client=self._connection._get_authenticated_client(),
        )
        self._check_response_is_valid(response)
        logger.info(f"Uploaded file {self.name} successfully deleted.")

    def update(self) -> None:
        """Updates the uploaded file properties from Igloo Cloud.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = fetch_uploaded_file.sync_detailed(
            workspace_id=self.workspace_id,
            file_id=self.id,
            client=self._connection._get_authenticated_client(),
        )
        raw_uploaded_file: ClientUploadedFile = self._validate_response(
            response, UploadedFileResponse, ClientUploadedFile
        )
        uploaded_file_dict = raw_uploaded_file.to_dict()

        self._update_properties_from_dict(uploaded_file_dict)

    async def _update_async(self) -> None:
        """Asynchronously updates the uploaded file properties from Igloo Cloud.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = await fetch_uploaded_file.asyncio_detailed(
            workspace_id=self.workspace_id,
            file_id=self.id,
            client=self._connection._get_authenticated_client(),
        )
        raw_uploaded_file: ClientUploadedFile = self._validate_response(
            response, UploadedFileResponse, ClientUploadedFile
        )
        uploaded_file_dict = raw_uploaded_file.to_dict()

        self._update_properties_from_dict(uploaded_file_dict)
