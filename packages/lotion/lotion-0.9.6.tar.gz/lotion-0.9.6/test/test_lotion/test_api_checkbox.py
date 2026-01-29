from unittest import TestCase

import pytest

from lotion.properties.checkbox import Checkbox
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiCheckbox(TestCase):
    DATABASE_ID = "15d6567a3bbf8075a116e8bbb4f76967"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    @pytest.mark.minimum()
    def test_チェックボックスを変更する(self):
        checkbox_prop = Checkbox.true(name="チェックボックス")
        actual = update_page(page=self.page, property=checkbox_prop)
        self.assertEqual(actual.get_checkbox(name="チェックボックス").checked, True)

        checkbox_false_prop = Checkbox.false(name="チェックボックス")
        actual = update_page(page=self.page, property=checkbox_false_prop)
        self.assertEqual(actual.get_checkbox(name="チェックボックス").checked, False)
