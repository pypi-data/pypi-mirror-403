from typing import Any, Callable, Optional, TypedDict

from typing_extensions import TypeAlias

OperatorFunction: TypeAlias = Callable[[Any], Any]
SensitivityOperatorFunction: TypeAlias = Callable[[Any, Any], Any]


class ColumnAdjustmentDict(TypedDict):
    function: "OperatorFunction"


class ColumnSensitivityDict(TypedDict):
    factors: list[Any]
    function: "SensitivityOperatorFunction"


class TableAdjustmentDict(TypedDict):
    columns: dict[str, "ColumnAdjustmentDict"]
    filter: Optional[Callable]


class TableSensitivityDict(TypedDict):
    columns: dict[str, "ColumnSensitivityDict"]
    filter: Optional[Callable]


RunAdjustmentDict: TypeAlias = dict[str, "TableAdjustmentDict"]
SensitivityDict: TypeAlias = dict[str, dict[str, "TableSensitivityDict"]]
