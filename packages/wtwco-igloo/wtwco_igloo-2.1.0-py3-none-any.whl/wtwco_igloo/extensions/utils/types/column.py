from __future__ import annotations

from dataclasses import dataclass

from wtwco_igloo.api_client.models import DataType


@dataclass
class Column:
    name: str
    display_name: str
    description: str
    data_type: DataType
    max_length: int | None
    file_type_specifier: str | None
    model_name: str | None
    minimum_version: str | None

    @classmethod
    def _from_dict(cls: type[Column], column_dict: dict) -> Column:
        return cls(
            name=column_dict.get("name") or "",
            display_name=column_dict["displayName"],
            description=column_dict.get("description", ""),
            data_type=DataType(column_dict["dataType"]),
            max_length=column_dict.get("maxLength"),
            file_type_specifier=column_dict.get("fileTypeSpecifier"),
            model_name=column_dict.get("modelName"),
            minimum_version=column_dict.get("minimumVersion"),
        )
