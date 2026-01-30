from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

if TYPE_CHECKING:
    from duckdb import DuckDBPyConnection, DuckDBPyRelation


@dataclass(frozen=True, slots=True)
class TillerDataset:
    _relation: DuckDBPyRelation

    def to_duckdb(
        self,
        *,
        con: DuckDBPyConnection | None = None,
    ) -> DuckDBPyRelation:
        if con is None:
            return self._relation
        return con.from_arrow(self._relation.fetch_arrow_table())

    def to_arrow(self) -> pa.Table:
        return self._relation.fetch_arrow_table()


@dataclass(frozen=True, slots=True)
class TillerData:
    _con: DuckDBPyConnection
    transactions: TillerDataset
    categories: TillerDataset

    @classmethod
    def fetch(cls, spreadsheet_url: str) -> TillerData:
        from .pipeline import _fetch_and_transform

        return _fetch_and_transform(spreadsheet_url=spreadsheet_url)
