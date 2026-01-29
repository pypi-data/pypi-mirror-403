from datetime import date, datetime
from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.datetime_utils import JST
from lotion.properties.date import Date
from lotion.properties.property import Property
from lotion.properties.title import Title


@pytest.mark.api()
class TestUpdateProperty(TestCase):
    DATABASE_ID = "1596567a3bbf80d58251f1159e5c40fa"
    PROP_NAME = "日付"

    def setUp(self) -> None:
        self.suite = Lotion.get_instance()
        created_page = self.suite.create_page_in_database(
            database_id=self.DATABASE_ID, properties=[Title.from_plain_text(text="テスト")]
        )
        self.page = self.suite.retrieve_page(page_id=created_page.id)
        return super().setUp()

    def tearDown(self) -> None:
        self.suite.remove_page(self.page.id)
        return super().setUp()

    @pytest.mark.minimum()
    def test_開始日を変更する(self):
        # Given
        date_ = date(2021, 1, 1)
        date_prop = Date.from_start_date(name=self.PROP_NAME, start_date=date_)

        # When, Then
        actual = self._update_page(property=date_prop)
        self.assertEqual(actual.start_date, date_)
        self.assertEqual(actual.start_time, date_)
        self.assertEqual(actual.start_datetime, datetime(2021, 1, 1, tzinfo=JST))
        self.assertEqual(actual.end_date, None)
        self.assertEqual(actual.end_datetime, None)
        self.assertEqual(actual.end_time, None)

    def test_開始時刻を変更する(self):
        # Given
        datetime_ = datetime(2021, 1, 1, 12, 34, 0, tzinfo=JST)
        date_prop = Date.from_start_date(name=self.PROP_NAME, start_date=datetime_)

        # When, Then
        actual = self._update_page(property=date_prop)
        self.assertEqual(actual.start_date, datetime_.date())
        print(actual.start_datetime)
        print(datetime_)
        self.assertEqual(actual.start_datetime, datetime_)
        self.assertEqual(actual.start_time, datetime_)
        self.assertEqual(actual.end_date, None)
        self.assertEqual(actual.end_datetime, None)
        self.assertEqual(actual.end_time, None)

    def test_開始日と終了日を変更する(self):
        # Given
        start_date = date(2021, 1, 1)
        end_date = date(2021, 1, 2)
        date_prop = Date.from_range(name=self.PROP_NAME, start=start_date, end=end_date)

        # When, Then
        actual = self._update_page(property=date_prop)
        self.assertEqual(actual.start_date, start_date)
        self.assertEqual(actual.start_time, start_date)
        self.assertEqual(actual.start_datetime, datetime(2021, 1, 1, tzinfo=JST))
        self.assertEqual(actual.end_date, end_date)
        self.assertEqual(actual.end_time, end_date)
        self.assertEqual(actual.end_datetime, datetime(2021, 1, 2, tzinfo=JST))

    def test_開始時刻と終了時刻を変更する(self):
        # Given
        start_datetime = datetime(2021, 1, 1, 12, 34, 0, tzinfo=JST)
        end_datetime = datetime(2021, 1, 1, 23, 45, 0, tzinfo=JST)
        date_prop = Date.from_range(
            name=self.PROP_NAME,
            start=start_datetime,
            end=end_datetime,
        )

        # When, Then
        actual = self._update_page(property=date_prop)
        self.assertEqual(actual.start_date, start_datetime.date())
        self.assertEqual(actual.start_time, start_datetime)
        self.assertEqual(actual.start_datetime, start_datetime)
        self.assertEqual(actual.end_date, end_datetime.date())
        self.assertEqual(actual.end_time, end_datetime)
        self.assertEqual(actual.end_datetime, end_datetime)

    def _update_page(self, property: Property):
        # When
        properties = self.page.properties.append_property(property)
        self.suite.update_page(page_id=self.page.id, properties=properties.values)

        # Then
        page = self.suite.retrieve_page(page_id=self.page.id)
        return page.get_date(name=self.PROP_NAME)
