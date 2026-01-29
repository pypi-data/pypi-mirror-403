import sys
from unittest import TestCase

sys.path.append("notion_api")

# クラス名の一致をチェックするロジックがあるので、完全に合わせておく
from lotion.properties.properties import Properties
from lotion.properties.title import Title


class TestProperties(TestCase):
    def setUp(self) -> None:
        title = Title.from_plain_text(name="名前", text="タイトル")
        self.suite = Properties(values=[title])
        return super().setUp()

    def test_プロパティを置換する(self):
        # Given
        new_title = Title.from_plain_text(name="名前", text="新しいタイトル")

        # When
        properties = self.suite.append_property(new_title)

        # Then
        # print(properties.values)
        self.assertEqual(1, len(properties.values))
        self.assertEqual("新しいタイトル", properties.get_title().text)
