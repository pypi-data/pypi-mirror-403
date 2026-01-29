from unittest import TestCase

import pytest

from lotion import Lotion, notion_database, notion_prop
from lotion.base_page import BasePage
from lotion.properties.multi_select import MultiSelect

DATABASE_ID = "15c6567a3bbf80818512f43db108616f"


@notion_prop("マルチセレクト")
class MyMultiSelect(MultiSelect):
    pass


@notion_database(DATABASE_ID)
class MyDatabase(BasePage):
    select: MyMultiSelect


@pytest.mark.api()
class TestApiMultiSelect(TestCase):
    def setUp(self) -> None:
        self.suite = Lotion.get_instance()

    @pytest.mark.minimum()
    def test_fetch_multi_select(self):
        actual = self.suite.fetch_multi_select(MyDatabase, MyMultiSelect, ["A", "B"])
        actual_name_list = [item.name for item in actual.values]
        self.assertTrue("A" in actual_name_list)
        self.assertTrue("B" in actual_name_list)

        # キャッシュの確認
        # result = self.suite.fetch_multi_select(MyDatabase, MyMultiSelect, "B")
        # self.fail("キャッシュの確認")
