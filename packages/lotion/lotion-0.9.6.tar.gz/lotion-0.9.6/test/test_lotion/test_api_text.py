import json
from unittest import TestCase

import pytest

from lotion.properties.text import Text
from lotion.properties.title import Title
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiText(TestCase):
    DATABASE_ID = "15d6567a3bbf80db8cb6d63ab1fecf22"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    @pytest.mark.minimum()
    def test_テキストを変更する(self):
        text_prop = Text.from_plain_text(name="テキスト", text="テスト")
        actual = update_page(page=self.page, property=text_prop)
        self.assertEqual(actual.get_text(name="テキスト").text, "テスト")

        text_empty_prop = Text.empty(name="テキスト")
        actual = update_page(page=self.page, property=text_empty_prop)
        self.assertEqual(actual.get_text(name="テキスト").text, "")

    @pytest.mark.minimum()
    def test_タイトルを変更する(self) -> None:
        # Given
        title = Title.from_mentioned_page(
            mentioned_page_id="1596567a3bbf80bb92a0d05094b0c110", prefix="prefix", suffix="suffix"
        )

        # When
        actual = update_page(page=self.page, property=title)
        print(json.dumps(actual.get_title().rich_text.to_dict(), ensure_ascii=False))
        for element in actual.get_title().rich_text.elements:
            print(element.to_plain_text())

        # Then
        self.assertEqual(actual.get_title().text, "prefixLotion開発用suffix")
