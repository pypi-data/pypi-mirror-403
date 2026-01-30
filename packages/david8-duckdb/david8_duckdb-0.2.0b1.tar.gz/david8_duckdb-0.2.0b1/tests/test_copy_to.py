from david8.protocols.sql import QueryProtocol
from parameterized import parameterized

from tests.base_test import BaseTest


class TestCopyTo(BaseTest):
    @parameterized.expand([
        (
            BaseTest.qb.copy_to('events', 'events.csv'),
            "COPY events TO 'events.csv'",
        ),
        (
            BaseTest.qb.copy_to('events', 'events.csv', {'DELIMITER': "','", 'APPEND': True}),
            "COPY events TO 'events.csv' (DELIMITER ',', APPEND true)",
        ),
        # query
        (
            BaseTest.qb.copy_to(
                BaseTest.qb.select('name', 'value').from_table('events'),
                'events.csv'
            ),
            "COPY (SELECT name, value FROM events) TO 'events.csv'"
        ),
        (
            BaseTest.qb.copy_to(
                BaseTest.qb.select('name', 'value').from_table('events'),
                'events.csv',
                {'DELIMITER': "','", 'APPEND': True},
            ),
            "COPY (SELECT name, value FROM events) TO 'events.csv' (DELIMITER ',', APPEND true)",
        ),
    ])
    def test_copy_to(self, query: QueryProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)
