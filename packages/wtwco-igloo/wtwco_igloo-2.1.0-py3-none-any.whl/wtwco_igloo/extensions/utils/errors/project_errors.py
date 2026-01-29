from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError


class ProjectError(WtwcoIglooError):
    "Base class for project errors."

    def __init__(self, *args):
        super().__init__(*args)


class ProjectParameterError(ProjectError):
    "Exception raised when project parameters are incorrect."

    def __init__(self, *args):
        super().__init__(*args)


class ProjectNotFoundError(ProjectError):
    "Exception raised when a project is not found."

    def __init__(self, *args):
        super().__init__(*args)


class ProjectHasNoRunsError(ProjectError):
    "Exception raised when a project has no runs."

    def __init__(self, *args):
        super().__init__(*args)


class ProjectDeletionError(ProjectError):
    "Exception raised when a project cannot be deleted"

    def __init__(self, *args):
        super().__init__(*args)


class DataTableNotFoundError(ProjectError):
    "Exception raised when a data table is not found."

    def __init__(self, *args):
        super().__init__(*args)


class ProjectNamingError(ProjectError, ValueError):
    "Exception raised when a project name is invalid."

    def __init__(self, *args):
        super().__init__(*args)
