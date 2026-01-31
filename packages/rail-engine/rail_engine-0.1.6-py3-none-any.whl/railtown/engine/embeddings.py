"""Embeddings API methods for Rail Engine."""

import logging
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Literal, Optional, Type

import httpx
from pydantic import BaseModel

from railtown.engine.utils import filter_items

if TYPE_CHECKING:
    from railtown.engine.client import Railengine

logger = logging.getLogger(__name__)


async def search_vector_store(
    client: "Railengine",
    engine_id: Optional[str] = None,
    vector_store: Literal["VectorStore1", "VectorStore2", "VectorStore3"] = "VectorStore1",
    query: str = "",
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
) -> AsyncIterator[Any]:
    """
    Search a vector store using the Railtown API.

    Args:
        client: Railengine client instance
        engine_id: Engine ID (uses client.engine_id if not provided)
        vector_store: Vector store name. Must be one of: "VectorStore1", "VectorStore2", "VectorStore3"
        query: Query string for semantic search
        filter_fn: Optional filter function that takes an item and returns bool
        model: Optional model type to override default model from client

    Yields:
        Search results (deserialized to model type if provided, otherwise dictionaries)
    """
    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    # Validate vector_store value
    valid_stores = {"VectorStore1", "VectorStore2", "VectorStore3"}
    if vector_store not in valid_stores:
        raise ValueError(f"vector_store must be one of {valid_stores}, got '{vector_store}'")

    endpoint = f"{client.api_url}/api/Engine/{engine_id}/Embeddings/Search"
    headers = client._get_headers()

    json_body = {
        "VectorStore": vector_store,
        "Query": query,
    }

    logger.info(f"Searching vector store {vector_store} for query: {query} (engine: {engine_id})")

    try:
        response = await client._client.post(
            endpoint, headers=headers, json=json_body, timeout=30.0
        )
        response.raise_for_status()

        result_data = response.json()

        # Extract items from response
        items = result_data.get("Items", []) if isinstance(result_data, dict) else []

        # Filter and deserialize items
        async for item in filter_items(
            iter(items),
            filter_fn=filter_fn,
            default_model=client.model,
            override_model=model,
        ):
            yield item

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error searching vector store: {e.response.status_code} - {e.response.text}"
        )
        # Return empty iterator on error (graceful degradation)
        return
    except httpx.RequestError as e:
        logger.error(f"Request error searching vector store: {str(e)}")
        # Return empty iterator on error (graceful degradation)
        return
    except Exception as e:
        logger.error(f"Error searching vector store: {str(e)}", exc_info=True)
        # Return empty iterator on error (graceful degradation)
        return
