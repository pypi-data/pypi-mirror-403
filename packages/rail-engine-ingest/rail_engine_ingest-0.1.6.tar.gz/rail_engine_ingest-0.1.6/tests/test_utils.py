"""Tests for utility functions."""

import pytest
from pydantic import BaseModel

from railtown.engine.utils import deserialize_item, filter_items


class FoodDiaryItem(BaseModel):
    """Test Pydantic model."""

    food_name: str
    calories: int
    carbs: float = 0.0


class FoodSummary(BaseModel):
    """Alternative test Pydantic model."""

    name: str
    cal: int


def test_deserialize_item_with_model():
    """Test deserializing item with Pydantic model."""
    item = {"food_name": "Apple", "calories": 95, "carbs": 25.0}

    result = deserialize_item(item, default_model=FoodDiaryItem)

    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Apple"
    assert result.calories == 95


def test_deserialize_item_without_model():
    """Test deserializing item without model returns dict."""
    item = {"food_name": "Apple", "calories": 95}

    result = deserialize_item(item)

    assert isinstance(result, dict)
    assert result == item


def test_deserialize_item_with_override_model():
    """Test deserializing item with override model."""
    item = {"food_name": "Apple", "calories": 95}

    result = deserialize_item(item, default_model=FoodDiaryItem, override_model=FoodSummary)

    # Should use override model, but FoodSummary needs different fields
    # This will fail validation, so it should return raw dict
    assert isinstance(result, dict)


def test_deserialize_item_handles_invalid_data():
    """Test deserializing item with invalid data returns raw dict."""
    item = {"invalid": "data"}

    result = deserialize_item(item, default_model=FoodDiaryItem)

    # Should return raw dict if validation fails
    assert isinstance(result, dict)
    assert result == item


@pytest.mark.asyncio
async def test_filter_items_without_filter():
    """Test filter_items without filter function."""
    items = [
        {"food_name": "Apple", "calories": 95},
        {"food_name": "Banana", "calories": 105},
    ]

    results = []
    async for item in filter_items(iter(items)):
        results.append(item)

    assert len(results) == 2
    assert results[0] == items[0]
    assert results[1] == items[1]


@pytest.mark.asyncio
async def test_filter_items_with_filter():
    """Test filter_items with filter function."""
    items = [
        {"food_name": "Apple", "calories": 95},
        {"food_name": "Banana", "calories": 105},
        {"food_name": "Pizza", "calories": 300},
    ]

    def high_calorie(item):
        return item.get("calories", 0) > 200

    results = []
    async for item in filter_items(iter(items), filter_fn=high_calorie):
        results.append(item)

    assert len(results) == 1
    assert results[0]["food_name"] == "Pizza"


@pytest.mark.asyncio
async def test_filter_items_with_model():
    """Test filter_items with Pydantic model."""
    items = [
        {"food_name": "Apple", "calories": 95},
        {"food_name": "Banana", "calories": 105},
    ]

    results = []
    async for item in filter_items(iter(items), default_model=FoodDiaryItem):
        results.append(item)

    assert len(results) == 2
    assert isinstance(results[0], FoodDiaryItem)
    assert results[0].food_name == "Apple"


@pytest.mark.asyncio
async def test_filter_items_with_model_and_filter():
    """Test filter_items with both model and filter."""
    items = [
        {"food_name": "Apple", "calories": 95},
        {"food_name": "Banana", "calories": 105},
        {"food_name": "Pizza", "calories": 300},
    ]

    def high_calorie(item):
        # Item will be FoodDiaryItem instance
        return item.calories > 200

    results = []
    async for item in filter_items(
        iter(items), filter_fn=high_calorie, default_model=FoodDiaryItem
    ):
        results.append(item)

    assert len(results) == 1
    assert isinstance(results[0], FoodDiaryItem)
    assert results[0].food_name == "Pizza"


@pytest.mark.asyncio
async def test_filter_items_with_override_model():
    """Test filter_items with override model."""
    items = [
        {"food_name": "Apple", "calories": 95},
    ]

    results = []
    async for item in filter_items(
        iter(items),
        default_model=FoodDiaryItem,
        override_model=FoodSummary,
    ):
        results.append(item)

    # FoodSummary needs different fields, so should return raw dict
    assert len(results) == 1
    assert isinstance(results[0], dict)


def test_deserialize_item_with_content_field():
    """Test deserializing item with 'content' field containing JSON string."""
    # API returns items with 'content' field as JSON string
    item = {
        "EngineDocumentId": "doc-123",
        "content": '{"food_name": "Apple", "calories": 95, "carbs": 25.0}',
    }

    result = deserialize_item(item, default_model=FoodDiaryItem)

    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Apple"
    assert result.calories == 95
    assert result.carbs == 25.0


def test_deserialize_item_with_content_field_pascalcase():
    """Test deserializing item with 'Content' field (PascalCase) containing JSON string."""
    # API may return 'Content' field (PascalCase) as JSON string
    item = {
        "EngineDocumentId": "doc-123",
        "Content": '{"food_name": "Banana", "calories": 105, "carbs": 27.0}',
    }

    result = deserialize_item(item, default_model=FoodDiaryItem)

    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Banana"
    assert result.calories == 105
    assert result.carbs == 27.0


def test_deserialize_item_with_content_field_invalid_json():
    """Test deserializing item with invalid JSON in 'content' field falls back to whole item."""
    # If content field has invalid JSON, should fall back to deserializing whole item
    item = {
        "EngineDocumentId": "doc-123",
        "content": "not valid json",
        "food_name": "Apple",
        "calories": 95,
    }

    result = deserialize_item(item, default_model=FoodDiaryItem)

    # Should fall back to deserializing whole item
    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Apple"
    assert result.calories == 95


def test_deserialize_item_with_content_field_as_dict():
    """Test deserializing item with 'content' field already as dict (not JSON string)."""
    # Some APIs may return content as dict instead of JSON string
    item = {
        "EngineDocumentId": "doc-123",
        "content": {"food_name": "Apple", "calories": 95, "carbs": 25.0},
    }

    result = deserialize_item(item, default_model=FoodDiaryItem)

    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Apple"
    assert result.calories == 95
