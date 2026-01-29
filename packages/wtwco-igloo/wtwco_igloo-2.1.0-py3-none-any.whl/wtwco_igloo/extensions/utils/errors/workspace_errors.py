from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError


class WorkspaceError(WtwcoIglooError):
    "Base class for workspace errors."

    def __init__(self, *args):
        super().__init__(*args)


class WorkspaceNotFoundError(WorkspaceError):
    "Exception raised when a workspace is not found."

    def __init__(self, *args):
        super().__init__(*args)
