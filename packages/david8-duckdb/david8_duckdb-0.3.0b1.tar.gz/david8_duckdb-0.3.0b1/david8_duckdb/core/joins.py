import dataclasses

from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import JoinProtocol


@dataclasses.dataclass(slots=True)
class PositionalJoin(JoinProtocol):
    table_name: str

    def get_sql(self, dialect: DialectProtocol) -> str:
        return f'POSITIONAL JOIN {dialect.quote_ident(self.table_name)}'
