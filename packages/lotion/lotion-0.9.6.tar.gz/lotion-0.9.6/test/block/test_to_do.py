from unittest import TestCase

from lotion.block.to_do import ToDo


class TestToDo(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test(self):
        # Given
        block_dict = {
            "object": "block",
            "id": "56696b99-a01d-4acc-8e8a-438e4aece59f",
            "parent": {
                "type": "page_id",
                "page_id": "470e7491-f533-4836-8f27-213ed8947ba6",
            },
            "created_time": "2024-06-04T01:38:00.000Z",
            "last_edited_time": "2024-06-04T01:39:00.000Z",
            "created_by": {
                "object": "user",
                "id": "6f877603-07b9-4467-b811-31706eeb640c",
            },
            "last_edited_by": {
                "object": "user",
                "id": "6f877603-07b9-4467-b811-31706eeb640c",
            },
            "has_children": False,
            "archived": False,
            "in_trash": False,
            "type": "to_do",
            "to_do": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "test", "link": None},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default",
                        },
                        "plain_text": "test",
                        "href": None,
                    }
                ],
                "checked": False,
                "color": "default",
            },
        }

        # When
        suite = ToDo.of(block_dict)
        actual = suite.to_dict()

        # Then
        self.assertTrue(actual["type"] == "to_do")
