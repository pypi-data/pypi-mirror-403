from typing import Any, Type

from pydantic import ValidationError

from wtwco_igloo.extensions.utils.errors.run_errors import RunInputDictionaryTypeError, RunInputDictionaryValueError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import _log_and_get_exception


class _InputValidator:
    @staticmethod
    def _validate(user_input: Any, validator_class: Type) -> None:
        attribute_to_set: str = list(validator_class.__annotations__.keys())[0]
        validator_instance = validator_class
        try:
            validator_instance(**{attribute_to_set: user_input})

        except ValidationError as e:
            error = e.errors()[0]
            if error["type"] == "value_error":
                raise _log_and_get_exception(RunInputDictionaryValueError, error["msg"]) from None
            else:
                raise _log_and_get_exception(
                    RunInputDictionaryTypeError,
                    "Type error in input dictionary.\n"
                    + f" Location: {'.'.join(map(str, error['loc']))}\n"
                    + f" {error['msg']} got {type(error['input'])}.",
                ) from None
