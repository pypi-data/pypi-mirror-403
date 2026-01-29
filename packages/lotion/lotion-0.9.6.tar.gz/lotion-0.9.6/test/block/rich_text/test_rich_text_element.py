from unittest import TestCase

import pytest

from lotion.block.rich_text.rich_text_element import RichTextElement, RichTextTextElement


class TestReadBlock(TestCase):
    @pytest.mark.minimum()
    def test_内部ページリンクを含むリッチテキストを扱える(self):
        # Given: Notion APIから返される内部ページリンクを含むテキスト要素
        input = {
            "type": "text",
            "text": {"content": "内部ページへのリンク", "link": {"page_id": "2ec6567a-3bbf-81b6-970c-cf6ad93ea8cc"}},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            "plain_text": "内部ページへのリンク",
            "href": "/2ec6567a3bbf81b6970ccf6ad93ea8cc",
        }

        # When
        rich_text = RichTextElement.from_entity(input)

        # Then
        self.assertIsInstance(rich_text, RichTextTextElement)
        self.assertEqual(rich_text.content, "内部ページへのリンク")
        self.assertEqual(rich_text.link_page_id, "2ec6567a-3bbf-81b6-970c-cf6ad93ea8cc")
        self.assertIsNone(rich_text.link_url)

    @pytest.mark.minimum()
    def test_内部ページリンクをAPIに送信できる形式に変換できる(self):
        # Given: 内部ページリンクを持つRichTextTextElement
        element = RichTextTextElement.of(
            content="内部ページへのリンク", link_page_id="2ec6567a-3bbf-81b6-970c-cf6ad93ea8cc"
        )

        # When
        result = element.to_dict()

        # Then
        self.assertEqual(result["type"], "text")
        self.assertEqual(result["text"]["content"], "内部ページへのリンク")
        self.assertEqual(result["text"]["link"]["page_id"], "2ec6567a-3bbf-81b6-970c-cf6ad93ea8cc")
        self.assertNotIn("url", result["text"]["link"])

    @pytest.mark.minimum()
    def test_外部URLリンクは従来通り動作する(self):
        # Given: 外部URLリンクを持つテキスト要素
        input = {
            "type": "text",
            "text": {"content": "外部リンク", "link": {"url": "https://example.com"}},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            "plain_text": "外部リンク",
            "href": "https://example.com",
        }

        # When
        rich_text = RichTextElement.from_entity(input)

        # Then
        self.assertIsInstance(rich_text, RichTextTextElement)
        self.assertEqual(rich_text.link_url, "https://example.com")
        self.assertIsNone(rich_text.link_page_id)

        # And: API送信形式でもurlが使われる
        result = rich_text.to_dict()
        self.assertEqual(result["text"]["link"]["url"], "https://example.com")
        self.assertNotIn("page_id", result["text"]["link"])

    @pytest.mark.minimum()
    def test_link_mentionのリッチテキストを扱える(self):
        # Given
        input = {
            "type": "mention",
            "mention": {
                "type": "link_mention",
                "link_mention": {
                    "href": "https://miro.com/app/board/uXjVMxYuGhI=/?moveToWidget=3458764560855121283&cot=14",
                    "title": "A private Miro board",
                    "padding": 75,
                    "icon_url": "https://miro.com/favicon.ico",
                    "iframe_url": "https://miro.com/app/live-embed/uXjVMxYuGhI=/?moveToWidget=3458764560855121283&cot=14&embedId=927451861288&embedSource=oembed&embedMode=view_only_without_ui",
                    "link_provider": "Miro",
                    "thumbnail_url": "https://miro.com/app/images/application/icons/board_vis_230905/board-ava.png",
                },
            },
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            "plain_text": "https://miro.com/app/board/uXjVMxYuGhI=/?moveToWidget=3458764560855121283&cot=14",
            "href": "https://miro.com/app/board/uXjVMxYuGhI=/?moveToWidget=3458764560855121283&cot=14",
        }

        # When
        rich_text = RichTextElement.from_entity(input)

        # Then
        self.assertEqual(
            rich_text.href, "https://miro.com/app/board/uXjVMxYuGhI=/?moveToWidget=3458764560855121283&cot=14"
        )
        self.assertEqual(rich_text.to_plain_text(), "A private Miro board")
