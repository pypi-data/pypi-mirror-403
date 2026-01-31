from david8_duckdb.joins import positional
from tests.base_test import BaseTest


class TestJoin(BaseTest):
    def test_positional(self):
        self.assertEqual(
            BaseTest.qb.select('*').from_table('table1').join(positional('pos_table')).get_sql(),
            'SELECT * FROM table1 POSITIONAL JOIN pos_table',
        )
