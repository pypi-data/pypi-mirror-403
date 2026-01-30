import dataclasses

from david8.core.base_query import BaseQuery
from david8.protocols.dialect import DialectProtocol

from david8_duckdb.protocols.sql import SelectProtocol


@dataclasses.dataclass(slots=True)
class CopyToQuery(BaseQuery):
    source: str | SelectProtocol
    target: str
    copy_options: dict = None

    def _render_sql(self, dialect: DialectProtocol) -> str:
        source = f'({self.source.get_sql(dialect)})' if isinstance(self.source, SelectProtocol) else self.source
        return f"COPY {source} TO '{self.target}'"

    def _render_sql_postfix(self, dialect: DialectProtocol) -> str:
        if not self.copy_options:
            return ''

        option_items = []
        for key, value in self.copy_options.items():
            if value is not None:
                fixed_value = str(value).lower() if isinstance(value, bool) else value
                option_items.append(f'{key} {fixed_value}')

        return f' ({", ".join(option_items)})'
