from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError


class UploadedFileError(WtwcoIglooError):
    "Base class for uploaded file errors."

    def __init__(self, *args):
        super().__init__(*args)


class UploadedFileNotFoundError(UploadedFileError):
    "Exception raised when an uploaded file is not found."

    def __init__(self, *args):
        super().__init__(*args)
