from unittest import TestCase

import pytest

from lotion.properties.number import Number
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiNumber(TestCase):
    DATABASE_ID = "15d6567a3bbf80189707fd2234965886"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    def test_数値を変更する(self):
        number_prop = Number.from_num(name="数値", value=1)
        actual = update_page(page=self.page, property=number_prop)
        self.assertEqual(actual.get_number(name="数値").number, 1)

        number_empty_prop = Number.empty(name="数値")
        actual = update_page(page=self.page, property=number_empty_prop)
        self.assertEqual(actual.get_number(name="数値").number, None)
