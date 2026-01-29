from unittest import TestCase

from lotion.properties.created_by import CreatedBy

# クラス名の一致をチェックするロジックがあるので、完全に合わせておく


class TestCreatedBy(TestCase):
    def test_of(self) -> None:
        key = "作成者"
        input = {
            "id": "VbPv",
            "type": "created_by",
            "created_by": {
                "object": "user",
                "id": "510806db-4772-4f42-b4b6-6f81b6e8b788",
                "name": "daily-api",
                "avatar_url": None,
                "type": "bot",
                "bot": {},
            },
        }
        actual = CreatedBy.of(key, input)

        # Then
        self.assertEqual(actual.id, "VbPv")
