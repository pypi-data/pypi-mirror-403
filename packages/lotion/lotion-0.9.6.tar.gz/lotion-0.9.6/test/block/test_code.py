from unittest import TestCase

import pytest

from lotion.block.code import Code


class TestCode(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    @pytest.mark.minimum()
    def test(self):
        # Given
        input = {
            "object": "block",
            "id": "83dc84f8-2bee-4ed4-9ea2-df66eafe6e72",
            "parent": {"type": "page_id", "page_id": "c560bb27-1b52-4d52-83a6-4b8e7615ea9d"},
            "created_time": "2024-03-08T06:43:00.000Z",
            "last_edited_time": "2024-03-08T06:43:00.000Z",
            "created_by": {"object": "user", "id": "6f877603-07b9-4467-b811-31706eeb640c"},
            "last_edited_by": {"object": "user", "id": "6f877603-07b9-4467-b811-31706eeb640c"},
            "has_children": False,
            "archived": False,
            "type": "code",
            "code": {
                "caption": [],
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": 'setcookie("user", "alex", time()+3600);', "link": None},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default",
                        },
                        "plain_text": 'setcookie("user", "alex", time()+3600);',
                        "href": None,
                    }
                ],
                "language": "php",
            },
        }

        # When
        actual = Code.of(input)

        # Then
        self.assertEqual(actual.type, "code")
        self.assertEqual(actual.language, "php")
        self.assertEqual(actual.rich_text.to_plain_text(), 'setcookie("user", "alex", time()+3600);')
        expected_slack_text = """```php
setcookie("user", "alex", time()+3600);
```"""
        self.assertEqual(actual.to_slack_text(), expected_slack_text)
        expected_sub_dict = {
            "rich_text": [
                {
                    "plain_text": 'setcookie("user", "alex", time()+3600);',
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "href": None,
                    "text": {"content": 'setcookie("user", "alex", time()+3600);', "link": None},
                    "type": "text",
                }
            ],
            "language": "php",
        }
        actual_sub_dict = actual.to_dict_sub()
        self.assertEqual(actual_sub_dict["language"], expected_sub_dict["language"])
        self.assertEqual(actual_sub_dict["rich_text"][0]["plain_text"], expected_sub_dict["rich_text"][0]["plain_text"])
