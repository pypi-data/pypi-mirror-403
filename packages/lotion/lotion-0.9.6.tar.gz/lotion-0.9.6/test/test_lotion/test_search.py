from datetime import date
from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.filter import Builder, Cond
from lotion.properties import Number, Text
from lotion.properties.date import Date
from lotion.properties.url import Url


@pytest.mark.api()
class TestSearch(TestCase):
    DATABASE_ID = "15d6567a3bbf8032ada3e0a42892c357"

    def setUp(self) -> None:
        self.suite = Lotion.get_instance()
        return super().setUp()

    @pytest.mark.minimum()
    def test_検索_シンプルなテキスト検索(self):
        # Given
        filter_param = {
            "property": "テキスト",
            "rich_text": {
                "contains": "A",
            },
        }
        self._search_and_assert(filter_param, 1)

    @pytest.mark.minimum()
    def test_検索_複数の条件指定(self):
        # Given
        text_prop = Text.from_plain_text("テスト", "名前")
        number_prop = Number.from_num(50, "数値")
        filter_param = (
            Builder.create()
            .add(prop=text_prop, cond=Cond.STARTS_WITH)
            .add(prop=number_prop, cond=Cond.GREATER_THAN)
            .build()
        )
        self._search_and_assert(filter_param, 1)

    def test_検索_日付の検索(self):
        # Given
        date_ = date.fromisoformat("2021-01-01")
        date_prop = Date.from_start_date(date_, "日付")
        filter_param = Builder.create().add(prop=date_prop, cond=Cond.AFTER).build()
        self._search_and_assert(filter_param, 1)

    def test_検索_日付の検索_1年前以内(self):
        # Given
        date_ = date.fromisoformat("2021-01-01")
        date_prop = Date.from_start_date(date_, "日付")
        filter_param = Builder.create().add(date_prop, Cond.PAST_YEAR).build()
        self._search_and_assert(filter_param, 0)

    def test_or条件(self):
        # Given
        text_prop_a = Text.from_plain_text("テストA", "名前")
        text_prop_b = Text.from_plain_text("テキストB", "テキスト")
        filter_param_a = Builder.create().add(prop=text_prop_a, cond=Cond.EQUALS).build()
        filter_param_b = Builder.create().add(prop=text_prop_b, cond=Cond.EQUALS).build()
        filter_param = {
            "or": [filter_param_a, filter_param_b],
        }
        self._search_and_assert(filter_param, 2)

    def test_最終更新日時で検索(self):
        # Given
        filter_param = Builder.create().add_last_edited_at(Cond.AFTER, "2021-01-01").build()
        self._search_and_assert(filter_param, 2)

    def test_urlの検索(self):
        # Given
        url = Url.from_url("https://example.com/", "url")
        filter_param = Builder.create().add(url, Cond.EQUALS).build()
        self._search_and_assert(filter_param, 1)

    def test_Urlを持つデータを検索(self):
        filter_param = Builder.create().add(Url, Cond.IS_NOT_EMPTY).build()
        self._search_and_assert(filter_param, 1)

    def _search_and_assert(self, filter_param: dict, expected: int):
        # When
        actual = self.suite.retrieve_database(
            database_id=self.DATABASE_ID,
            filter_param=filter_param,
        )

        # Then
        self.assertEqual(expected, len(actual))
