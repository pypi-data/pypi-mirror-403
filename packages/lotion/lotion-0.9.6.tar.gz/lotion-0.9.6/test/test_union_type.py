"""Tests for Union type handling in @notion_database decorator."""

from unittest import TestCase

import pytest

from lotion import notion_database, notion_prop
from lotion.base_page import BasePage
from lotion.properties.properties import Properties
from lotion.properties.select import Select


# Sample property class for testing
@notion_prop("タイミング")
class SomedayTiming(Select):
    pass


# Test class with Union type annotation (Python 3.10+ syntax)
@notion_database("dummy-database-id")
class PageWithUnionType(BasePage):
    timing: SomedayTiming | None = None


# Test class with Optional type annotation (Python 3.9 compatible)
@notion_database("dummy-database-id-2")
class PageWithOptionalType(BasePage):
    timing: SomedayTiming | None = None


# Test class with non-union type annotation
@notion_database("dummy-database-id-3")
class PageWithNonUnionType(BasePage):
    timing: SomedayTiming


@pytest.mark.minimum()
class TestUnionType(TestCase):
    def test_union_type_property_access_does_not_raise_attribute_error(self):
        """Union型(X | None)のプロパティにアクセスしてもAttributeErrorが発生しない"""
        # Given: A page with properties including the timing property
        timing_prop = SomedayTiming.from_name(name="タイミング", selected_name="朝")
        page = PageWithUnionType(
            properties=Properties(values=[timing_prop]),
        )

        # When: Accessing the timing property
        result = page.timing

        # Then: No AttributeError should be raised and result should be the property
        self.assertIsNotNone(result)
        self.assertEqual(result.selected_name, "朝")

    def test_optional_type_property_access_does_not_raise_attribute_error(self):
        """Optional[X]のプロパティにアクセスしてもAttributeErrorが発生しない"""
        # Given: A page with properties including the timing property
        timing_prop = SomedayTiming.from_name(name="タイミング", selected_name="朝")
        page = PageWithOptionalType(
            properties=Properties(values=[timing_prop]),
        )

        # When: Accessing the timing property
        result = page.timing

        # Then: No AttributeError should be raised and result should be the property
        self.assertIsNotNone(result)
        self.assertEqual(result.selected_name, "朝")

    def test_non_union_type_property_access_still_works(self):
        """通常の型のプロパティへのアクセスも正常に動作する"""
        # Given: A page with properties including the timing property
        timing_prop = SomedayTiming.from_name(name="タイミング", selected_name="朝")
        page = PageWithNonUnionType(
            properties=Properties(values=[timing_prop]),
        )

        # When: Accessing the timing property
        result = page.timing

        # Then: Result should be the property
        self.assertIsNotNone(result)
        self.assertEqual(result.selected_name, "朝")

    def test_union_type_property_setter_works(self):
        """Union型プロパティのセッターが正常に動作する"""
        # Given: A page with an initial timing property
        timing_prop = SomedayTiming.from_name(name="タイミング", selected_name="朝")
        page = PageWithUnionType(
            properties=Properties(values=[timing_prop]),
        )

        # When: Setting a new timing value
        new_timing = SomedayTiming.from_name(name="タイミング", selected_name="夜")
        page.timing = new_timing

        # Then: The property should be updated
        result = page.timing
        self.assertEqual(result.selected_name, "夜")
