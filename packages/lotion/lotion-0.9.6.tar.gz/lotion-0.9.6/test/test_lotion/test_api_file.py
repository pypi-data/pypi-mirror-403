from unittest import TestCase

import pytest

from lotion.lotion import Lotion
from lotion.properties.title import Title
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiStatus(TestCase):
    DATABASE_ID = "1636567a3bbf8094bad4cac512a79539"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    def test_ファイルのあるページを変更できる(self):
        title = Title.from_plain_text(text="テスト")
        actual = update_page(page=self.page, property=title)
        self.assertEqual(actual.get_title().text, "テスト")

    def test_ファイルプロパティを取得できる(self):
        page = Lotion.get_instance().retrieve_page(page_id="1636567a3bbf80aeb2ccce5c0320bfc5")
        files = page.get_files(name="ファイル&メディア").value
        self.assertEqual(len(files), 2)
