from unittest import TestCase

import pytest

from lotion.properties.email import Email
from lotion.properties.phone_number import PhoneNumber
from test.test_lotion.lotion_utils import create_empty_page, remove_page, update_page


@pytest.mark.api()
class TestApiEmailAndPhone(TestCase):
    DATABASE_ID = "15d6567a3bbf80bf94b8f2d46d195724"

    def setUp(self) -> None:
        self.page = create_empty_page(database_id=self.DATABASE_ID)
        return super().setUp()

    def tearDown(self) -> None:
        remove_page(page_id=self.page.id)
        return super().setUp()

    def test_メールを変更する(self):
        email_prop = Email.from_email(name="メール", email="sample@example.com")
        actual = update_page(page=self.page, property=email_prop)
        self.assertEqual(actual.get_email(name="メール").value, "sample@example.com")

        email_empty_prop = Email.empty(name="メール")
        actual = update_page(page=self.page, property=email_empty_prop)
        self.assertEqual(actual.get_email(name="メール").value, "")

    def test_電話番号を変更する(self):
        phone_number_prop = PhoneNumber.create(name="電話", phone_number="090-1234-5678")
        actual = update_page(page=self.page, property=phone_number_prop)
        self.assertEqual(actual.get_phone_number(name="電話").value, "090-1234-5678")

        phone_number_empty_prop = PhoneNumber.empty(name="電話")
        actual = update_page(page=self.page, property=phone_number_empty_prop)
        self.assertEqual(actual.get_phone_number(name="電話").value, "")
