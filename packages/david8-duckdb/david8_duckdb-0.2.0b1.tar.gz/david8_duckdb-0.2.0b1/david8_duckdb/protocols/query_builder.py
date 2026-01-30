from david8.protocols.query_builder import QueryBuilderProtocol as _QueryBuilderProtocol
from david8.protocols.sql import AliasedProtocol, ExprProtocol, FunctionProtocol, QueryProtocol

from ..protocols.sql import SelectProtocol


class QueryBuilderProtocol(_QueryBuilderProtocol):
    def select(self, *args: str | AliasedProtocol | ExprProtocol | FunctionProtocol) -> SelectProtocol:
        pass

    def copy_to(self, source: str | SelectProtocol, target: str, copy_options: dict = None) -> QueryProtocol:
        """
        :param source: query or table
        :param target: file name
        :param copy_options: https://duckdb.org/docs/stable/sql/statements/copy#copy--to-options

        example:
            qb.copy_to('events', 'events.parquet', {'FORMAT': 'parquet', 'DELIMITER': "','", 'APPEND': True})
        """
