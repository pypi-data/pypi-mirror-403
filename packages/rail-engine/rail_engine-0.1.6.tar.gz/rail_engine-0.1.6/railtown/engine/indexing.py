"""Indexing API methods for Rail Engine."""

import logging
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from railtown.engine.utils import filter_items

if TYPE_CHECKING:
    from railtown.engine.client import Railengine

logger = logging.getLogger(__name__)


async def search_index(
    client: "Railengine",
    project_id: str = "",
    engine_id: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
) -> AsyncIterator[Any]:
    """
    Search index using the Railtown API.

    Args:
        client: Railengine client instance
        project_id: Project ID (required)
        engine_id: Engine ID (uses client.engine_id if not provided)
        query: Query dictionary (e.g., {"search": "example", "filter": "..."})
        filter_fn: Optional filter function that takes an item and returns bool
        model: Optional model type to override default model from client

    Yields:
        Search results (deserialized to model type if provided)
    """
    if not project_id:
        logger.error("project_id is required for index search")
        return

    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    endpoint = f"{client.api_url}/api/Engine/Indexing/Search"
    headers = client._get_headers()

    json_body = {
        "ProjectId": project_id,
        "EngineId": engine_id,
        "Query": query or {},
    }

    logger.info(f"Searching index for project {project_id}, engine {engine_id}, query: {query}")

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
        logger.error(f"HTTP error searching index: {e.response.status_code} - {e.response.text}")
        # Return empty iterator on error (graceful degradation)
        return
    except httpx.RequestError as e:
        logger.error(f"Request error searching index: {str(e)}")
        # Return empty iterator on error (graceful degradation)
        return
    except Exception as e:
        logger.error(f"Error searching index: {str(e)}", exc_info=True)
        # Return empty iterator on error (graceful degradation)
        return
