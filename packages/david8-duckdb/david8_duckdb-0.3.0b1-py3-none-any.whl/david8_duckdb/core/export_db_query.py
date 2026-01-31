import dataclasses

from david8.core.base_query import BaseQuery
from david8.protocols.dialect import DialectProtocol

from .query_options_processor import options_to_str


@dataclasses.dataclass(slots=True)
class ExportImportDbQuery(BaseQuery):
    name: str
    export: bool = True
    options: dict | None = None

    def _render_sql(self, dialect: DialectProtocol) -> str:
        return f"{'EXPORT' if self.export else 'IMPORT'} DATABASE '{self.name}'"

    def _render_sql_postfix(self, dialect: DialectProtocol) -> str:
        return options_to_str(self.options)
