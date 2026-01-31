from david8.protocols.sql import JoinProtocol

from .core.joins import PositionalJoin as _PositionalJoin


def positional(table_name: str) -> JoinProtocol:
    """
    https://duckdb.org/docs/stable/sql/query_syntax/from#positional-joins
    """
    return _PositionalJoin(table_name)
