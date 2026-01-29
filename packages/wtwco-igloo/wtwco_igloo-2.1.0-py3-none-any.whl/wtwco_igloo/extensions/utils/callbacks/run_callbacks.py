import os
from logging import Logger
from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from logging import Logger

    from wtwco_igloo import UploadedFile, Workspace


class FileReferenceCopyPolicy(Protocol):
    """Resolves file references when copying data between workspaces.

    This protocol defines the signature for callbacks that handle file references
    during cross-workspace copying operations. Implementations should determine
    how to resolve file references in the alternate workspace.

    Args:
        original_file: The file from the source workspace
        existing_file: The file in the alternate workspace (if it exists)
        folder_path: Optional folder path to upload files from
        workspace: The alternate workspace. Can be used to upload files.
        logger:

    Returns:
        The file name to use in the destination run
    """

    def __call__(
        self,
        original_file: "UploadedFile",
        existing_file: Optional["UploadedFile"],
        folder_path: Optional[str],
        workspace: "Workspace",
        logger: Logger,
    ) -> str: ...


def default_file_reference_copy_policy(
    original_file: "UploadedFile",
    existing_file: Optional["UploadedFile"],
    folder_path: Optional[str],
    workspace: "Workspace",
    logger: "Logger",
) -> str:
    """Default callback to resolve file references when copying data between workspaces.

    This callback implements a three-tier resolution policy for file references:
    1. If a file with the same name exists in the alternate workspace, use that file.
    2. If a folder_path is provided and the file exists there, upload it to the alternate workspace.
    3. Otherwise, blank the file reference and log a warning.

    Args:
        original_file: The file from the source workspace
        existing_file: The file in the alternate workspace (if it exists)
        folder_path: Optional folder path to upload files from
        workspace: The alternate workspace. Can be used to upload files.
        logger:

    Returns:
        The resolved file name to use in the alternate workspace, or empty string if the file cannot be resolved.
    """
    # If the file exists in the workspace, reference that file
    if existing_file is not None:
        return existing_file.name

    # If no folder is provided, we blank the reference
    if folder_path is None:
        logger.warning(
            f"File {original_file.name} not found in alternate workspace, and no folder has been provided. File reference will be blanked"
        )
        return ""

    file_name_and_ext = os.path.join(folder_path, original_file.name + original_file.extension)

    # If the file exists in the local folder, upload and reference that file
    if os.path.exists(file_name_and_ext):
        try:
            logger.info(f"Attempting to upload file '{file_name_and_ext}' to workspace '{workspace.name}'")
            uploaded_files = workspace.upload_files(file_name_and_ext)
            # Return the name of the only file that was uploaded
            (file_name,) = uploaded_files.keys()
            return file_name
        except Exception as e:
            logger.warning(f"Failed to upload file '{file_name_and_ext}': {e}. File reference will be blanked.")
            return ""

    # Otherwise, blank the file reference and warn
    logger.warning(
        f"File '{original_file.name}' does not exist in workspace or local folder. File reference will be blanked."
    )
    return ""
