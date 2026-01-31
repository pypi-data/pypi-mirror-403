import dataclasses
from collections.abc import Iterable
from typing import Any

from david8.core.base_query import BaseQuery
from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import ExprProtocol, LogicalOperatorProtocol, PredicateProtocol

from david8_duckdb.protocols.sql import MergeIntoProtocol, SelectProtocol


@dataclasses.dataclass(slots=True)
class _MatchedExpr(ExprProtocol):
    then: str
    operator: LogicalOperatorProtocol | None = None
    not_: bool = False
    set_columns: dict[str, Any] = dataclasses.field(default_factory=dict)

    def get_sql(self, dialect: DialectProtocol) -> str:
        items = ['WHEN', f'{"NOT " if self.not_ else ""}MATCHED']
        for item in [
            f'AND {self.operator.get_sql(dialect)}' if self.operator else '',
            'THEN',
            self.then,
        ]:
            if item:
                items.append(item)

        if self.set_columns:
            items.append('SET')
            columns = []
            for key, value in self.set_columns.items():
                if isinstance(value, ExprProtocol):
                    right_col = value.get_sql(dialect)
                else:
                    right_col = dialect.quote_ident(value)

                columns.append(f'{dialect.quote_ident(key)} = {right_col}')

            items.append(', '.join(columns))
        return ' '.join(items)


@dataclasses.dataclass(slots=True)
class MergeIntoQuery(BaseQuery, MergeIntoProtocol):
    table: str
    source_value: SelectProtocol | None = None
    source_as: str = ''
    using_columns: Iterable[str] = dataclasses.field(default_factory=tuple)
    on_columns: tuple[LogicalOperatorProtocol | PredicateProtocol, ...] = dataclasses.field(default_factory=tuple)
    returning_value: tuple[str, ...] = dataclasses.field(default_factory=tuple)
    matched: tuple[_MatchedExpr, ...] = dataclasses.field(default_factory=tuple)

    def _render_sql(self, dialect: DialectProtocol) -> str:
        items = [f"MERGE INTO {dialect.quote_ident(self.table)}"]
        for item in [
            self._using_to_sql(dialect),
            f"ON ({' AND '.join(on.get_sql(dialect) for on in self.on_columns)})" if self.on_columns else "",
            self._matched_to_sql(dialect),
            f'RETURNING {", ".join(self.returning_value)}' if self.returning_value else ''
        ]:
            if item:
                items.append(item)
        return ' '.join(items)

    def _matched_to_sql(self, dialect: DialectProtocol) -> str:
        if not self.matched:
            return ''

        return f"{' '.join(m.get_sql(dialect) for m in self.matched)}"

    def _using_to_sql(self, dialect: DialectProtocol) -> str:
        if not self.source_value:
            return ''

        columns = ''
        if self.using_columns:
            columns = ', '.join(dialect.quote_ident(c) for c in self.using_columns)
            columns = f' USING ({columns})'

        return f'USING ({self.source_value.get_sql(dialect)}) AS {self.source_as}{columns}'

    def using(self, query: SelectProtocol, as_: str, columns: Iterable[str] | None = None) -> 'MergeIntoProtocol':
        self.source_value = query
        self.source_as = as_
        if columns:
            self.using_columns = columns
        return self

    def on(self, *args: LogicalOperatorProtocol | PredicateProtocol) -> 'MergeIntoProtocol':
        self.on_columns += args
        return self

    def update_when_matched(
        self,
        operator: LogicalOperatorProtocol | None = None,
        columns: dict[str, Any] | None = None,
    ) -> 'MergeIntoProtocol':
        self.matched += (_MatchedExpr('UPDATE', operator, set_columns=columns or {}),)
        return self

    def delete_when_matched(self, operator: LogicalOperatorProtocol) -> 'MergeIntoProtocol':
        self.matched += (_MatchedExpr('DELETE', operator),)
        return self

    def returning(self, *args: str) -> 'MergeIntoProtocol':
        self.returning_value = args
        return self

    def insert_when_not_matched(self) -> 'MergeIntoProtocol':
        self.matched += (_MatchedExpr('INSERT', not_=True),)
        return self

