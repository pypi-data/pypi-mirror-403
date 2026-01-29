from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError


class ModelError(WtwcoIglooError):
    "Base class for model errors."

    def __init__(self, *args):
        super().__init__(*args)


class ModelNotFoundError(ModelError):
    "Exception raised when a model is not found."

    def __init__(self, *args):
        super().__init__(*args)
