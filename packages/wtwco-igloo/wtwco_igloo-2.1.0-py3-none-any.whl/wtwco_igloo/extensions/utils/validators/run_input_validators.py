from typing import Any, Callable, Optional

from pydantic import BaseModel, Field, field_validator


### Sensitivity validators
class ColumnSensitivityDictValidator(BaseModel):
    factors: list[Any] = Field(..., description="List of factors to apply to the column")
    function: Callable[[Any, Any], Any] = Field(..., description="Function to apply to the column")

    @field_validator("factors")
    @classmethod
    def check_factors_not_empty(cls, value: list[Any]) -> list[Any]:
        if not value:
            raise ValueError("Input dictionary value error: The 'factors' list must not be empty")
        return value


class TableSensitivityDictValidator(BaseModel):
    columns: dict[str, ColumnSensitivityDictValidator] = Field(
        ..., description="Dictionary of columns to apply factors and function on"
    )
    filter: Optional[Callable[[Any], bool]] = Field(None, description="Filter to apply to the table")

    @field_validator("columns")
    @classmethod
    def check_columns_not_empty(
        cls, value: dict[str, ColumnSensitivityDictValidator]
    ) -> dict[str, ColumnSensitivityDictValidator]:
        if not value:
            raise ValueError("Input dictionary value error: The 'columns' dictionary must not be empty")
        return value


class SensitivityDictValidator(BaseModel):
    sensitivity_dict: dict[str, dict[str, TableSensitivityDictValidator]] = Field(
        ..., description="Dictionary of scenarios"
    )

    @field_validator("sensitivity_dict")
    @classmethod
    def check_sensitivity_dict_not_empty(
        cls, value: dict[str, dict[str, TableSensitivityDictValidator]]
    ) -> dict[str, dict[str, TableSensitivityDictValidator]]:
        if not value:
            raise ValueError("Input dictionary value error: The 'sensitivity_dict' dictionary must not be empty")
        return value


### Adjustment validators
class ColumnAdjustmentDictValidator(BaseModel):
    function: Callable[[Any], Any] = Field(..., description="Function to apply to the column")


class TableAdjustmentDictValidator(BaseModel):
    columns: dict[str, ColumnAdjustmentDictValidator] = Field(
        ..., description="Dictionary of columns to apply function on"
    )
    filter: Optional[Callable[[Any], bool]] = Field(None, description="Filter to apply to the table")

    @field_validator("columns")
    @classmethod
    def check_columns_not_empty(
        cls, value: dict[str, ColumnAdjustmentDictValidator]
    ) -> dict[str, ColumnAdjustmentDictValidator]:
        if not value:
            raise ValueError("Input dictionary value error: The 'columns' dictionary must not be empty")
        return value


class RunAdjustmentDictValidator(BaseModel):
    run_adjustment_dict: dict[str, TableAdjustmentDictValidator] = Field(..., description="Dictionary of adjustments")

    @field_validator("run_adjustment_dict")
    @classmethod
    def check_run_adjustment_dict_not_empty(
        cls, value: dict[str, TableAdjustmentDictValidator]
    ) -> dict[str, TableAdjustmentDictValidator]:
        if not value:
            raise ValueError("Input dictionary value error: The 'run_adjustment_dict' dictionary must not be empty")
        return value
