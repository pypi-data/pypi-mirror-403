from david8.core.base_query_builder import BaseQueryBuilder as _BaseQueryBuilder
from david8.protocols.sql import AliasedProtocol, ExprProtocol, FunctionProtocol, QueryProtocol

from ..protocols.query_builder import QueryBuilderProtocol
from ..protocols.sql import MergeIntoProtocol, PivotProtocol, SelectProtocol, UnpivotProtocol
from .copy_to_query import CopyToQuery
from .dml import MergeIntoQuery
from .dql import PivotQuery, UnpivotQuery
from .export_db_query import ExportImportDbQuery
from .select_query import DuckDbSelect


class DuckDbQueryBuilder(QueryBuilderProtocol, _BaseQueryBuilder):
    def select(self, *args: str | AliasedProtocol | ExprProtocol | FunctionProtocol) -> SelectProtocol:
        return DuckDbSelect(select_columns=args, dialect=self._dialect)

    def copy_to(self, source: str | SelectProtocol, target: str, copy_options: dict | None = None) -> QueryProtocol:
        return CopyToQuery(dialect=self._dialect, source=source, target=target, copy_options=copy_options)

    def export_db(self, name: str, options: dict | None = None) -> QueryProtocol:
        return ExportImportDbQuery(dialect=self._dialect, name=name, options=options)

    def import_db(self, name: str) -> QueryProtocol:
        return ExportImportDbQuery(dialect=self._dialect, name=name, export=False)

    def merge_into(self, table: str) -> MergeIntoProtocol:
        return MergeIntoQuery(dialect=self._dialect, table=table)

    def pivot(self, table: str) -> PivotProtocol:
        return PivotQuery(dialect=self._dialect, table=table)

    def unpivot(self, table: str) -> UnpivotProtocol:
        return UnpivotQuery(dialect=self._dialect, table=table)
