from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import InvalidFileError, WtwcoIglooError


class UploaderError(WtwcoIglooError):
    "Base class for run errors."

    def __init__(self, *args):
        super().__init__(*args)


class InvalidZipFileError(InvalidFileError, UploaderError):
    "Exception raised when a file is not a ZIP file."

    def __init__(self, *args):
        super().__init__(*args)
