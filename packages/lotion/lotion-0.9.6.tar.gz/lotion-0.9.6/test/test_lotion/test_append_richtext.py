from datetime import date
from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.block.paragraph import Paragraph
from lotion.block.rich_text.rich_text_builder import RichTextBuilder


@pytest.mark.api()
class TestAppendBlock(TestCase):
    PAGE_ID = "1636567a3bbf80e8b2f3eb7b0587e8d2"

    def setUp(self):
        self.suite = Lotion.get_instance()
        # self.suite.clear_page(self.PAGE_ID)

    # def test_test(self):
    #     page = self.suite.retrieve_page(self.PAGE_ID)
    #     for block in page.block_children:
    #         if isinstance(block, Paragraph):
    #             print(block)
    #             for rich_text in block.rich_text.to_dict():
    #                 print(rich_text)
    #     # self.fail()

    def test_日付メンションを追加する(self):
        today = date.today()
        builder = RichTextBuilder.create()
        builder = builder.add_date_mention(start=today)
        builder = builder.add_text(content="テスト")
        rich_text = builder.build()
        self.suite.append_block(block_id=self.PAGE_ID, block=Paragraph(rich_text=rich_text))

    def test_できあがったRichTextの先頭に文字を追加(self):
        rich_text = RichTextBuilder.create().add_text("テスト").build()
        rich_text = RichTextBuilder.create().add_text("prefix").add_rich_text(rich_text).build()
        self.suite.append_block(block_id=self.PAGE_ID, block=Paragraph(rich_text=rich_text))
