from parameterized import parameterized

from david8_duckdb.protocols.sql import SelectProtocol
from tests.base_test import BaseTest


class TestSelect(BaseTest):
    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_csv('faulty.csv'),
            "SELECT * FROM read_csv('faulty.csv')",
        ),
        (
            BaseTest.qb.select('*').from_csv('flights1.csv', 'flights2.csv'),
            "SELECT * FROM read_csv(['flights1.csv', 'flights2.csv'])",
        ),
    ])
    def test_from_csv(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_json('todos.json'),
            "SELECT * FROM read_json('todos.json')",
        ),
        (
            BaseTest.qb.select('*').from_json('todos1.json', 'todos2.json'),
            "SELECT * FROM read_json(['todos1.json', 'todos2.json'])",
        ),
    ])
    def test_from_json(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_json_objects('todos.json'),
            "SELECT * FROM read_json_objects('todos.json')",
        ),
        (
            BaseTest.qb.select('*').from_json_objects('todos1.json', 'todos2.json'),
            "SELECT * FROM read_json_objects(['todos1.json', 'todos2.json'])",
        ),
    ])
    def test_from_json_objects(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_ndjson_objects('todos.json'),
            "SELECT * FROM read_ndjson_objects('todos.json')",
        ),
        (
            BaseTest.qb.select('*').from_ndjson_objects('todos1.json', 'todos2.json'),
            "SELECT * FROM read_ndjson_objects(['todos1.json', 'todos2.json'])",
        ),
    ])
    def test_from_ndjson_objects(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_json_objects_auto('todos.json'),
            "SELECT * FROM read_json_objects_auto('todos.json')",
        ),
        (
            BaseTest.qb.select('*').from_json_objects_auto('todos1.json', 'todos2.json'),
            "SELECT * FROM read_json_objects_auto(['todos1.json', 'todos2.json'])",
        ),
    ])
    def test_from_json_objects_auto(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_parquet('file.parquet'),
            "SELECT * FROM read_parquet('file.parquet')",
        ),
        (
            BaseTest.qb.select('*').from_parquet('file1.parquet', 'file2.parquet'),
            "SELECT * FROM read_parquet(['file1.parquet', 'file2.parquet'])",
        ),
    ])
    def test_from_parquet(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)

    @parameterized.expand([
        (
            BaseTest.qb.select('*').from_xlsx('test.xlsx'),
            "SELECT * FROM read_xlsx('test.xlsx')",
        ),
    ])
    def test_from_xlsx(self, query: SelectProtocol, exp_sql: str):
        self.assertEqual(query.get_sql(), exp_sql)
