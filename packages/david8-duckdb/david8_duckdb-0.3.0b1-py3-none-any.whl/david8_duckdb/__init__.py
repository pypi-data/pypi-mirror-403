from david8.core.base_dialect import BaseDialect as _BaseDialect
from david8.param_styles import QMarkParamStyle

from .core.query_builder import DuckDbQueryBuilder as _QueryBuilder
from .protocols.query_builder import QueryBuilderProtocol


def get_qb(is_quote_mode: bool = False) -> QueryBuilderProtocol:
    dialect = _BaseDialect(QMarkParamStyle(), is_quote_mode)
    return _QueryBuilder(dialect)
