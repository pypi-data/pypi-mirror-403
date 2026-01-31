from parameterized import parameterized

from david8_duckdb.protocols.sql import SelectProtocol
from tests.base_test import BaseTest


class TestExportImportDb(BaseTest):
    @parameterized.expand([
        (
            BaseTest.qb.export_db('target_directory'),
            "EXPORT DATABASE 'target_directory'",
        ),
        (
            BaseTest.qb.export_db('target_directory', {'FORMAT': 'csv', 'DELIMITER': "'|'"}),
            "EXPORT DATABASE 'target_directory' (FORMAT csv, DELIMITER '|')",
        ),
    ])
    def test_export_db(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    def test_import_db(self):
        self.assertEqual(
            BaseTest.qb.import_db('target_directory').get_sql(),
            "IMPORT DATABASE 'target_directory'"
        )
