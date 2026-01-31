from david8.functions import sum_

from tests.base_test import BaseTest


class TestDQL(BaseTest):
    def test_pivot(self):
        query = (
            BaseTest
            .qb
            .pivot('cities')
            .on('country', 'name')
            .using(
                sum_('population').as_('total'),
                sum_('population').as_('max'),
            )
            .group_by('country')
            .order_by('total')
            .order_by('country', desc=False)
            .limit(10)
        )

        self.assertEqual(
            query.get_sql(),
            'PIVOT cities '
            'ON country, name '
            'USING sum(population) AS total, sum(population) AS max '
            'GROUP BY country '
            'ORDER BY total DESC, country '
            'LIMIT 10'
        )

    def test_unpivot(self):
        query = (
            BaseTest
            .qb
            .unpivot('monthly_sales')
            .on('jan', 'feb', 'mar', 'apr', 'may', 'jun')
            .into('month', 'sales')
            .order_by('sales')
            .order_by('month', desc=False)
            .limit(10)
        )

        self.assertEqual(
            query.get_sql(),
            'UNPIVOT monthly_sales '
            'ON jan, feb, mar, apr, may, jun '
            'INTO NAME month '
            'VALUE sales '
            'ORDER BY sales DESC, month '
            'LIMIT 10'
        )
