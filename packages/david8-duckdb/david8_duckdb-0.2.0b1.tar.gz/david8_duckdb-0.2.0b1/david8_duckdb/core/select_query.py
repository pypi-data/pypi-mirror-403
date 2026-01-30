import dataclasses

from david8.core.base_dql import BaseSelect as _BaseSelect
from david8.protocols.dialect import DialectProtocol

from ..protocols.sql import SelectProtocol


@dataclasses.dataclass(slots=True)
class DuckDbSelect(_BaseSelect, SelectProtocol):
    from_files: tuple[str, tuple[str, ...]] = dataclasses.field(default_factory=tuple)

    def from_csv(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_csv', file_names)
        return self

    def from_json(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_json', file_names)
        return self

    def from_json_objects(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_json_objects', file_names)
        return self

    def from_ndjson_objects(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_ndjson_objects', file_names)
        return self

    def from_json_objects_auto(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_json_objects_auto', file_names)
        return self

    def from_parquet(self, *file_names: str) -> 'SelectProtocol':
        self.from_files = ('read_parquet', file_names)
        return self

    def from_xlsx(self, file_name: str) -> 'SelectProtocol':
        self.from_files = ('read_xlsx', (file_name,))
        return self

    def _from_to_sql(self, dialect: DialectProtocol) -> str:
        if not self.from_files:
            return _BaseSelect._from_to_sql(self, dialect)

        if len(self.from_files[1]) > 1:
            files = str(list(self.from_files[1]))
        else:
            files = f"'{self.from_files[1][0]}'"

        return f' FROM {self.from_files[0]}({files})'
