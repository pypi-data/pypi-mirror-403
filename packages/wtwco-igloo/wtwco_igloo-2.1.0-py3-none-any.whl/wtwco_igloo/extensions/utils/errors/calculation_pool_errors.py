from wtwco_igloo.extensions.utils.errors.run_errors import PoolNotFoundError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import WtwcoIglooError


class CalculationPoolError(WtwcoIglooError):
    """Base class for Calculation Pool errors."""


# We inherit from PoolNotFoundError to prevent making a breaking change here
class CalculationPoolNotFoundError(CalculationPoolError, PoolNotFoundError):
    def __init__(self, *args):
        super().__init__(*args)
