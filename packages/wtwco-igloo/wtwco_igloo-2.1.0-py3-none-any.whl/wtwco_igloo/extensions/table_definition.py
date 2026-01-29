from __future__ import annotations

from dataclasses import dataclass

from wtwco_igloo.api_client.models import TableType
from wtwco_igloo.extensions.utils.types.column import Column


@dataclass
class TableDefinition:
    table_type: TableType
    dimensions: list[Column]
    values: list[Column]

    @classmethod
    def _from_dict(cls: type[TableDefinition], table_dict: dict) -> TableDefinition:
        return cls(
            table_type=TableType(table_dict["tableType"]),
            dimensions=[Column._from_dict(dim) for dim in table_dict["dimensions"]],
            values=[Column._from_dict(col) for col in table_dict["values"]],
        )
