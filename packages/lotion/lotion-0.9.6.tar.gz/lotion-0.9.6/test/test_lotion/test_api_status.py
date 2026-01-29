from unittest import TestCase

import pytest

from lotion.properties.status import Status
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiStatus(TestCase):
    DATABASE_ID = "15d6567a3bbf80c18391ec4c8d780e6a"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    def test_ステータスを変更する(self):
        status_prop = Status.from_status_name(name="ステータス", status_name="未着手")
        actual = update_page(page=self.page, property=status_prop)
        self.assertEqual(actual.get_status(name="ステータス").status_name, "未着手")
