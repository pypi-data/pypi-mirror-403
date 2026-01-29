from unittest import TestCase

import pytest

from lotion import Lotion
from lotion.properties import Relation


@pytest.mark.api()
class TestApiRelationAndRollup(TestCase):
    DATABASE_ID = "15d6567a3bbf804e942dc49d808bf73a"

    def setUp(self) -> None:
        self.suite = Lotion.get_instance()

    @pytest.mark.minimum()
    def test_リレーションを変更する(self):
        page = self.suite.create_page_in_database(database_id=self.DATABASE_ID)

        # Given
        page_id = "15d6567a-3bbf-8041-91c4-e0dbd42644fe"
        relation_prop = Relation.from_id(name="リレーション", id=page_id)

        # When, Then
        properties = page.properties.append_property(relation_prop)
        self.suite.update_page(page_id=page.id, properties=properties.values)
        actual = self.suite.retrieve_page(page_id=page.id)
        actual_relation = actual.get_relation(name="リレーション")
        self.assertEqual(actual_relation.id_list, [page_id])

    def test_ロールアップを取得する(self):
        # When
        page_id = "15d6567a3bbf80c98c16d9b846d73946"
        page = self.suite.retrieve_page(page_id=page_id)

        # Then: 2が取得できること
        actual = page.get_rollup(name="ロールアップ_計算")
        self.assertEqual(actual.value, 2)

        # Then: 【消さない】リレーションA、【消さない】リレーションBが取得できること
        actual = page.get_rollup(name="ロールアップ_文字列")
        title_elements = [v["title"][0] for v in actual.value]
        text_contents = [t["text"]["content"] for t in title_elements]
        import json

        print(json.dumps(text_contents, indent=2, ensure_ascii=False))
        self.assertEqual(text_contents, ["【消さない】リレーションA", "【消さない】リレーションB"])
