from unittest import TestCase

import pytest

from lotion import Lotion, notion_database, notion_prop
from lotion.base_page import BasePage
from lotion.properties.select import Select

DATABASE_ID = "15a6567a3bbf80b4a76fc106b37fb92f"


@notion_prop("セレクト")
class MySelect(Select):
    pass


@notion_database(DATABASE_ID)
class MyDatabase(BasePage):
    select: MySelect


@pytest.mark.api()
class TestApiSelect(TestCase):
    def setUp(self) -> None:
        self.suite = Lotion.get_instance()

    @pytest.mark.minimum()
    def test_fetch_select(self):
        result = self.suite.fetch_select(MyDatabase, MySelect, "セレクトA")
        self.assertEqual(result.selected_name, "セレクトA")

        # キャッシュの確認
        # result = self.suite.fetch_select(MyDatabase, MySelect, "セレクトA")
        # self.fail("キャッシュの確認")
