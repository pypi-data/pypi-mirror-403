from datetime import date, datetime
from unittest import TestCase

import pytest

from lotion.properties.date import Date

DUMMY_START_DATE = date(2021, 1, 1)
DUMMY_END_DATE = date(2021, 1, 2)
DUMMY_START_DATETIME = datetime(2022, 1, 1, 1, 0, 0)
DUMMY_END_DATETIME = datetime(2022, 1, 1, 1, 0, 0)


class TestDate(TestCase):
    @pytest.mark.minimum()
    def test_range(self):
        # Given, When
        actual = Date.from_range(start=DUMMY_START_DATE, end=DUMMY_END_DATE)

        # Then
        self.assertEqual(DUMMY_START_DATE, actual.start_time)
        self.assertEqual(DUMMY_START_DATE, actual.start_date)

    @pytest.mark.minimum()
    def test_range_startがNoneなのにendが指定されている場合(self):
        # Then: expected raise ValueError
        with self.assertRaises(ValueError):
            # Given, When
            _ = Date.from_range(start=None, end=DUMMY_END_DATE)
