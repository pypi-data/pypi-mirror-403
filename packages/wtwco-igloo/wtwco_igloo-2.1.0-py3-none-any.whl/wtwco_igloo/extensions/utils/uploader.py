import asyncio
import os
import zipfile
from asyncio.events import AbstractEventLoop
from typing import Optional, Union

import aiofiles
from azure.storage.blob.aio import BlobClient

from wtwco_igloo import Connection, UploadedFile
from wtwco_igloo.api_client.api.uploaded_files import (
    create_uploaded_file,
    start_upload,
    update_upload_progress,
)
from wtwco_igloo.api_client.models import (
    CreateUploadedFile,
    Upload,
    UploadedFileResponse,
    UploadProgress,
    UploadResponse,
)
from wtwco_igloo.api_client.models import (
    UploadedFile as ClientUploadedFile,
)
from wtwco_igloo.extensions.utils.errors.uploader_errors import InvalidZipFileError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import (
    FilePathNotFoundError,
    FolderNotFoundError,
    InvalidFileError,
    UnexpectedResponseError,
    _log_and_get_exception,
)
from wtwco_igloo.extensions.utils.helpers import _validate_files_exist
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator


class _Uploader:
    def __init__(
        self,
        workspace_id: int,
        connection: Connection,
        event_loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        self._workspace_id = workspace_id
        self._connection = connection
        self._check_response_is_valid = _ResponseValidator._check_response_is_valid
        self._validate_response = _ResponseValidator._validate_response
        self._using_custom_loop = event_loop is not None
        self._event_loop = event_loop if event_loop else asyncio.new_event_loop()

    def __enter__(self) -> "_Uploader":
        return self

    def __exit__(self) -> None:
        if not self._using_custom_loop:
            self._event_loop.close()

    def _upload_folder(self, folder_path: str, folder_description: str = "") -> dict[str, "UploadedFile"]:
        if not os.path.isdir(folder_path):
            raise _log_and_get_exception(FolderNotFoundError, f"{folder_path} folder does not exist.")
        return self._upload_files([(file, folder_description) for file in self._get_all_files_in_folder(folder_path)])

    def _upload_files(self, files_and_descriptions: list[Union[str, tuple[str, str]]]) -> dict[str, "UploadedFile"]:
        return self._event_loop.run_until_complete(self._upload_files_async(files_and_descriptions))

    async def _upload_files_async(
        self, files_and_descriptions: list[Union[str, tuple[str, str]]]
    ) -> dict[str, "UploadedFile"]:
        formatted_files_and_descriptions, shared_folder = self._validate_and_format_input(files_and_descriptions)

        upload_tuples = await asyncio.gather(
            *[
                self._upload_file_async(file_and_description, shared_folder)
                for file_and_description in formatted_files_and_descriptions
            ]
        )
        return {file_name: uploaded_file for file_name, uploaded_file in upload_tuples}

    async def _upload_file_async(
        self, file_and_description: tuple[str, str], shared_folder: Optional[str] = None
    ) -> tuple[str, "UploadedFile"]:
        file, description = file_and_description
        file_name, file_extension = os.path.splitext(
            os.path.relpath(file, shared_folder) if shared_folder else os.path.basename(file)
        )
        # Get file id by creating upload
        create_upload_response = await create_uploaded_file.asyncio_detailed(
            workspace_id=self._workspace_id,
            client=self._connection._get_authenticated_client(),
            body=CreateUploadedFile(
                name=file_name, extension=file_extension, description=description, make_name_unique=True
            ),
        )

        raw_uploaded_file: ClientUploadedFile = self._validate_response(
            create_upload_response, UploadedFileResponse, ClientUploadedFile
        )
        uploaded_file = UploadedFile(raw_uploaded_file.to_dict(), self._connection)

        # Get Azure SAS URL and upload identifier
        start_upload_response = await start_upload.asyncio_detailed(
            workspace_id=self._workspace_id,
            file_id=uploaded_file.id,
            client=self._connection._get_authenticated_client(),
        )
        start_upload_response_result: Upload = self._validate_response(start_upload_response, UploadResponse, Upload)

        if isinstance(start_upload_response_result.sas_link, str) and isinstance(
            start_upload_response_result.identifier, str
        ):
            # Upload to blob storage
            blob_client = BlobClient.from_blob_url(blob_url=start_upload_response_result.sas_link)
            async with aiofiles.open(file, "rb") as data:
                await blob_client.upload_blob(data)

            # tell Igloo Cloud that the file has been uploaded
            complete_upload_response = await update_upload_progress.asyncio_detailed(
                workspace_id=self._workspace_id,
                file_id=uploaded_file.id,
                upload_identifier=start_upload_response_result.identifier,
                client=self._connection._get_authenticated_client(),
                body=UploadProgress(upload_percent=100),
            )
            self._check_response_is_valid(complete_upload_response)

            await uploaded_file._update_async()

            return (file_name, uploaded_file)

        else:
            raise _log_and_get_exception(
                UnexpectedResponseError,
                "Unexpected response from start_upload: sas_link and identifier must be strings.",
            )

    def _validate_and_format_input(
        self, files_and_descriptions: list[Union[str, tuple[str, str]]]
    ) -> tuple[list[tuple[str, str]], str]:
        formatted_files_and_descriptions = self._format_files_and_descriptions(files_and_descriptions)
        files = [file for file, _ in formatted_files_and_descriptions]
        _validate_files_exist(files)
        self._validate_file_types(files)
        shared_folder = os.path.commonpath(files) if len(files) > 1 else ""

        return formatted_files_and_descriptions, shared_folder

    @staticmethod
    def _validate_file_types(files: list[str]) -> None:
        non_csv_files = [file for file in files if not str(file).endswith(".csv")]
        non_zip_or_csv_files = [file for file in non_csv_files if not str(file).endswith(".zip")]

        if len(non_zip_or_csv_files) > 0:
            raise _log_and_get_exception(
                InvalidFileError,
                f"Only csv and zip files are accepted for uploading. The following files are not csv or zip: \
                    {', '.join(non_zip_or_csv_files)}.",
            )

        for zip_file in non_csv_files:
            try:
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    zipped_files = zip_ref.namelist()
                    if (
                        all(file.endswith(".igx") or file.endswith(".igy") for file in zipped_files)
                        and len(zipped_files) > 0
                    ):
                        continue
                    else:
                        raise _log_and_get_exception(
                            InvalidZipFileError,
                            f"Zip file is empty or contains invalid files. Only .igx and .igy files are accepted for \
                            zip uploading. The following files are not accepted:\
                                {', '.join(zip_ref.namelist())}.",
                        )
            except zipfile.BadZipFile:
                raise _log_and_get_exception(InvalidZipFileError, f"{zip_file} is not a valid zip file.") from None

    @staticmethod
    def _get_all_files_in_folder(folder_path: str) -> list[str]:
        return [os.path.join(root, file) for root, _, files in os.walk(folder_path) for file in files]

    @staticmethod
    def _format_files_and_descriptions(
        files_and_descriptions: list[Union[str, tuple[str, str]]],
    ) -> list[tuple[str, str]]:
        if not files_and_descriptions:
            raise _log_and_get_exception(FilePathNotFoundError, "File path(s) were not provided.")

        return [
            (os.path.abspath(file_and_description), "")
            if isinstance(file_and_description, str)
            else (os.path.abspath(file_and_description[0]), file_and_description[1])
            for file_and_description in files_and_descriptions
        ]
