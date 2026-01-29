from unittest import TestCase

# https://developers.notion.com/reference/post-database-query-filter
from lotion.filter import Builder, Cond
from lotion.properties.text import Text


class TestBuilder(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_タイトルで絞りこむ(self):
        text_prop = Text.from_plain_text("テストA", "名前")
        actual = Builder.create().add(prop=text_prop, cond=Cond.EQUALS).build()
        expected = {
            "property": "名前",
            "rich_text": {
                "equals": "テストA",
            },
        }
        self.assertEqual(expected, actual)

    def test_作成日時で絞り込む(self):
        actual = Builder.create().add_created_at(cond_type=Cond.ON_OR_BEFORE, value="2024-12-16").build()
        expected = {
            "timestamp": "created_time",
            "created_time": {
                "on_or_before": "2024-12-16",
            },
        }
        self.assertEqual(expected, actual)

    def test_and条件で絞り込む(self):
        text_prop_a = Text.from_plain_text("テストA", "名前")
        text_prop_b = Text.from_plain_text("テストB", "名前")
        actual = (
            Builder.create().add(prop=text_prop_a, cond=Cond.EQUALS).add(prop=text_prop_b, cond=Cond.EQUALS).build()
        )
        print(actual)
        expected = {
            "and": [
                {
                    "property": "名前",
                    "rich_text": {"equals": "テストA"},
                },
                {
                    "property": "名前",
                    "rich_text": {"equals": "テストB"},
                },
            ],
        }
        self.assertEqual(expected, actual)

    def test_or条件で絞り込む(self):
        text_prop_a = Text.from_plain_text("テストA", "名前")
        text_prop_b = Text.from_plain_text("テストB", "名前")
        actual = (
            Builder.create()
            .add(prop=text_prop_a, cond=Cond.EQUALS)
            .add(prop=text_prop_b, cond=Cond.EQUALS)
            .build(mode="or")
        )
        expected = {
            "or": [
                {
                    "property": "名前",
                    "rich_text": {"equals": "テストA"},
                },
                {
                    "property": "名前",
                    "rich_text": {"equals": "テストB"},
                },
            ],
        }
        self.assertEqual(expected, actual)
