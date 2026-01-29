from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.base_page import BasePage


@pytest.mark.api()
@pytest.mark.current
class TestReadBlock(TestCase):
    def setUp(self):
        self.suite = Lotion.get_instance()

    @pytest.mark.minimum()
    def test_ページを取得する(self):
        page_id = "17c6567a3bbf805bbf21ceb23453ec8c"
        page = self.suite.retrieve_page(page_id=page_id)
        self.assertIsInstance(page, BasePage)
