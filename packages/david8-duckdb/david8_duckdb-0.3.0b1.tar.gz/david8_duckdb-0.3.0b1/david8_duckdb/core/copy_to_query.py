import dataclasses

from david8.core.base_query import BaseQuery
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import SelectProtocol
from .query_options_processor import options_to_str


@dataclasses.dataclass(slots=True)
class CopyToQuery(BaseQuery):
    source: str | SelectProtocol
    target: str
    copy_options: dict | None = None

    def _render_sql(self, dialect: DialectProtocol) -> str:
        source = f'({self.source.get_sql(dialect)})' if isinstance(self.source, SelectProtocol) else self.source
        return f"COPY {source} TO '{self.target}'"

    def _render_sql_postfix(self, dialect: DialectProtocol) -> str:
        return options_to_str(self.copy_options)
