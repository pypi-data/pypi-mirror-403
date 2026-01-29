from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError
from wtwco_igloo.logger import logger


class RunError(WtwcoIglooError):
    "Base class for run errors."

    def __init__(self, *args):
        super().__init__(*args)


class RunNotFoundError(RunError):
    "Exception raised when a run is not found."

    def __init__(self, *args):
        super().__init__(*args)


# Do not raise this error directly, it is superseded by calculation_pool_errors.CalculationPoolNotFoundError
class PoolNotFoundError(RunError):
    "Exception raised when a pool is not found."

    def __init__(self, *args):
        super().__init__(*args)


class OutputDataTableError(RunError):
    "Exception raised when outputting data tables fails."

    def __init__(self, *args):
        super().__init__(*args)


class RunDeletionError(RunError):
    "Exception raised when deleting a run fails."

    def __init__(self, message, error_info):
        super().__init__(message, error_info)

    def _log_error(self):
        logger.error(self.message)

    @property
    def message(self):
        return self.args[0]

    @property
    def error_info(self):
        return self.args[1]


class DataTransformationError(RunError, ValueError):
    "Exception raised when data transformation fails."

    def __init__(self, *args):
        super().__init__(*args)


class RunNamingError(RunError, ValueError):
    "Exception raised when a run name is invalid."

    def __init__(self, *args):
        super().__init__(*args)


class RunInputDictionaryKeyError(RunError, KeyError):
    "Exception raised when an input dictionary does not have a matching key."

    def __init__(self, *args):
        super().__init__(*args)


class RunInputDictionaryTypeError(RunError, TypeError):
    "Exception raised when an input dictionary is of the wrong type."

    def __init__(self, *args):
        super().__init__(*args)


class RunInputDictionaryValueError(RunError, ValueError):
    "Exception raised when an input dictionary contains an incorrect value."

    def __init__(self, *args):
        super().__init__(*args)


class UnrecognisedAdjustmentFunctionError(RunError):
    "Exception raised when an unrecognised adjustment operator is used."

    def __init__(self, *args):
        super().__init__(*args)


class RunParameterError(RunError):
    "Exception raised when run parameters are incorrect."

    def __init__(self, *args):
        super().__init__(*args)


class RunStateTimeOutError(RunError):
    "Exception raised when runs are still processing after the total wait time limit."

    def __init__(self, *args):
        super().__init__(*args)


class InvalidNodeOperationError(RunError, ValueError):
    "Exception raised when an invalid operation is attempted on a run result table node."

    def __init__(self, *args):
        super().__init__(*args)
