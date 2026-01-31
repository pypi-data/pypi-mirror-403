"""Utility functions for Rail Engine SDK."""

import json
from typing import Any, AsyncIterator, Callable, Dict, Iterator, Optional, Type

from pydantic import BaseModel


def deserialize_item(
    item: Dict[str, Any],
    default_model: Optional[Type[BaseModel]] = None,
    override_model: Optional[Type[BaseModel]] = None,
) -> Any:
    """
    Deserialize a dictionary item to a Pydantic model or return as dict.

    The API returns items with a 'content' field (JSON string) containing the actual user data.
    If a model is provided, this function parses the content field and deserializes it to the model.
    If no model is provided, returns the raw item dictionary.

    Args:
        item: Dictionary item to deserialize (may contain 'content' field with JSON string)
        default_model: Default model type (from client initialization)
        override_model: Override model type (from method call)

    Returns:
        Pydantic model instance if model provided, otherwise raw dictionary
    """
    # Use override model if provided, otherwise use default model
    model = override_model or default_model

    if model:
        # Check if item has a 'content' field (or 'Content' for compatibility)
        # The API returns user data in the content field as a JSON string
        content = item.get("content") or item.get("Content")

        if content:
            try:
                # Parse the JSON string from content field
                content_dict = json.loads(content) if isinstance(content, str) else content
                # Deserialize the parsed content to the model
                return model(**content_dict)
            except (json.JSONDecodeError, Exception) as e:
                # If parsing fails, try deserializing the whole item
                try:
                    return model(**item)
                except Exception:
                    # If that also fails, return raw dict
                    return item
        else:
            # No content field, try deserializing the whole item
            try:
                return model(**item)
            except Exception:
                # If deserialization fails, return raw dict
                return item

    return item


async def filter_items(
    items: Iterator[Dict[str, Any]],
    filter_fn: Optional[Callable[[Any], bool]] = None,
    default_model: Optional[Type[BaseModel]] = None,
    override_model: Optional[Type[BaseModel]] = None,
) -> AsyncIterator[Any]:
    """
    Filter and deserialize items from an iterator.

    Args:
        items: Iterator of dictionary items
        filter_fn: Optional filter function
        default_model: Default model type for deserialization
        override_model: Override model type for deserialization

    Yields:
        Filtered and deserialized items
    """
    for item in items:
        # Deserialize first
        deserialized = deserialize_item(item, default_model, override_model)

        # Apply filter if provided
        if filter_fn is None or filter_fn(deserialized):
            yield deserialized
