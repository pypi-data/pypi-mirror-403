from unittest import TestCase

import pytest

from lotion.properties.url import Url
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestUpdateProperty(TestCase):
    DATABASE_ID = "15d6567a3bbf80b9b213fcd260e2358e"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    def test_URLを変更する(self):
        url_prop = Url.from_url(name="URL", url="https://example.com")
        actual = update_page(page=self.page, property=url_prop)
        self.assertEqual(actual.get_url(name="URL").url, "https://example.com")

        url_empty_prop = Url.empty(name="URL")
        actual = update_page(page=self.page, property=url_empty_prop)
        self.assertEqual(actual.get_url(name="URL").url, "")
