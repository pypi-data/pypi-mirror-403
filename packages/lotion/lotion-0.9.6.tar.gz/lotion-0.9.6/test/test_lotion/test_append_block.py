from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.block import (
    Bookmark,
    BulletedListItem,
    Callout,
    Code,
    Divider,
    Embed,
    Heading,
    Image,
    NumberedListItem,
    Paragraph,
    Quote,
    ToDo,
    Video,
)


@pytest.mark.api()
class TestAppendBlock(TestCase):
    PAGE_ID = "1596567a3bbf8049803de1ffe3616d9e"

    def setUp(self):
        self.suite = Lotion.get_instance()
        self.suite.clear_page(self.PAGE_ID)

    @pytest.mark.minimum()
    def test_ブロックを追加する(self):
        blocks = []
        blocks.append(Paragraph.from_plain_text(text="テスト"))
        blocks.append(Bookmark.from_url(url="https://www.google.com/"))
        blocks.append(BulletedListItem.from_plain_text(text="テスト1"))
        blocks.append(BulletedListItem.from_plain_text(text="テスト2"))
        blocks.append(Divider())
        blocks.append(Embed.from_url(url="https://www.google.com/"))
        blocks.append(Heading.from_plain_text(heading_size=1, text="テスト"))
        blocks.append(Image.from_external_url(url="https://d3swar8tu7yuby.cloudfront.net/IMG_6286_thumb.jpg"))
        blocks.append(NumberedListItem.from_plain_text(text="テスト1"))
        blocks.append(NumberedListItem.from_plain_text(text="テスト2"))
        blocks.append(Quote.from_plain_text(text="テスト"))
        blocks.append(ToDo.from_plain_text(text="テスト1"))
        blocks.append(ToDo.from_plain_text(text="テスト2", checked=True))
        blocks.append(Video.from_external_url(url="https://www.youtube.com/watch?v=L5mF2uBKhS8"))
        blocks.append(Callout.from_plain_text(text="テスト"))
        blocks.append(Code.from_plain_text(text="print('hello')", language="python"))

        for i in range(len(blocks)):
            self.suite.append_block(block_id=self.PAGE_ID, block=blocks[i])

        page = self.suite.retrieve_page(self.PAGE_ID)
        for i in range(len(blocks)):
            self.assertIsInstance(page.block_children[i], blocks[i].__class__)
