from david8.logical_operators import and_
from david8.predicates import eq_c, gt, lt

from tests.base_test import BaseTest


class TestDML(BaseTest):
    def test_merge_into_using(self):
        query = (
            BaseTest
            .qb
            .merge_into('people')
            .using(
                BaseTest.qb.select('r_id', 'c_id', 'salary').from_table('id_table'),
                as_='deletes',
                columns=['r_id', 'c_id'],
            )
            .update_when_matched(and_(lt('people.salary', 100)), {'salary': 'upserts.salary'})
            .delete_when_matched(and_(gt('people.salary', 101)))
            .returning('merge_action', '*')
        )

        self.assertEqual(
            query.get_sql(),
            'MERGE INTO people '
            'USING (SELECT r_id, c_id, salary FROM id_table) AS deletes '
            'USING (r_id, c_id) '
            'WHEN MATCHED AND (people.salary < ?) THEN UPDATE SET salary = upserts.salary '
            'WHEN MATCHED AND (people.salary > ?) THEN DELETE '
            'RETURNING merge_action, *'
        )

        self.assertEqual(query.get_tuple_parameters(), (100, 101))

    def test_merge_into_on(self):
        query = (
            BaseTest
            .qb
            .merge_into('people')
            .using(
                BaseTest.qb.select('r_id', 'c_id', 'salary').from_table('id_table'),
                'deletes',
            )
            .on(
                eq_c('people.r_id', 'deletes.r_id'),
                eq_c('people.c_id', 'deletes.c_id'),
            )
            .update_when_matched(and_(lt('people.salary', 100)), {'salary': 'upserts.salary'})
            .delete_when_matched(and_(gt('people.salary', 101)))
        )

        self.assertEqual(
            query.get_sql(),
            'MERGE INTO people '
            'USING (SELECT r_id, c_id, salary FROM id_table) AS deletes '
            'ON (people.r_id = deletes.r_id AND people.c_id = deletes.c_id) '
            'WHEN MATCHED AND (people.salary < ?) THEN UPDATE SET salary = upserts.salary '
            'WHEN MATCHED AND (people.salary > ?) THEN DELETE'
        )

        self.assertEqual(query.get_tuple_parameters(), (100, 101))

    def test_merge_into_insert(self):
        query = (
            BaseTest
            .qb
            .merge_into('people')
            .using(
                BaseTest.qb.select('id').from_table('id_table'),
                as_='deletes',
                columns=['id'],
            )
            .insert_when_not_matched()
        )

        self.assertEqual(
            query.get_sql(),
            'MERGE INTO people '
            'USING (SELECT id FROM id_table) AS deletes '
            'USING (id) '
            'WHEN NOT MATCHED THEN INSERT',
        )
