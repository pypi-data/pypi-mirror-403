"""Tests for storage API methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from railtown.engine.client import Railengine
from railtown.engine.storage import (
    get_storage_document_by_customer_key,
    get_storage_document_by_event_id,
    list_storage_documents,
    query_storage_by_jsonpath,
)


@pytest.fixture
def mock_client(sample_pat, sample_engine_id):
    """Create a mock Railengine client."""
    with patch("railtown.engine.storage.httpx.AsyncClient") as mock_client_class:
        mock_http_client = AsyncMock()
        mock_client_class.return_value = mock_http_client

        client = Railengine(pat=sample_pat, engine_id=sample_engine_id)
        client._client = mock_http_client
        yield client, mock_http_client


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_success(mock_client):
    """Test getting storage document by EventId successfully."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple"}',
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="event-123"
    )

    assert result is not None
    assert result["EventId"] == "event-123"
    mock_http_client.get.assert_called_once()
    # Verify EventId parameter was used
    call_args = mock_http_client.get.call_args
    assert "EventId" in call_args.kwargs["params"]
    assert call_args.kwargs["params"]["EventId"] == "event-123"


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_not_found(mock_client):
    """Test getting storage document by EventId when not found."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_http_client.get = AsyncMock(return_value=mock_response)

    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="event-123"
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_with_filter(mock_client):
    """Test getting storage document by EventId with filter."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple", "calories": 95}',
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        return doc.get("Content", "").find("Apple") != -1

    result = await get_storage_document_by_event_id(
        client,
        engine_id=client.engine_id,
        event_id="event-123",
        filter_fn=filter_fn,
    )

    assert result is not None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_filter_rejects(mock_client):
    """Test get_storage_document_by_event_id with filter function that returns False."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple", "calories": 95}',
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        # Filter out documents with calories < 100
        return doc.get("Content", "").find('"calories": 200') != -1

    result = await get_storage_document_by_event_id(
        client,
        engine_id=client.engine_id,
        event_id="event-123",
        filter_fn=filter_fn,
    )

    # Filter should reject this document (calories is 95, not 200)
    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_http_400_error(mock_client):
    """Test get_storage_document_by_event_id handles HTTP 400 Bad Request."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request: Invalid event ID"
    # raise_for_status() should raise HTTPStatusError for non-2xx status codes
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=mock_response
    )
    mock_http_client.get = AsyncMock(return_value=mock_response)

    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="invalid-id"
    )

    # Should return None on HTTP error (not raise exception)
    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_http_401_error(mock_client):
    """Test get_storage_document_by_event_id handles HTTP 401 Unauthorized."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    # raise_for_status() should raise HTTPStatusError for non-2xx status codes
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )
    mock_http_client.get = AsyncMock(return_value=mock_response)

    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="event-123"
    )

    # Should return None on HTTP error (not raise exception)
    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_http_500_error(mock_client):
    """Test get_storage_document_by_event_id handles HTTP 500 Server Error."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    # raise_for_status() should raise HTTPStatusError for non-2xx status codes
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=MagicMock(), response=mock_response
    )
    mock_http_client.get = AsyncMock(return_value=mock_response)

    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="event-123"
    )

    # Should return None on HTTP error (not raise exception)
    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_request_error(mock_client):
    """Test get_storage_document_by_event_id handles request errors gracefully."""
    client, mock_http_client = mock_client

    error = httpx.RequestError("Connection error")
    mock_http_client.get = AsyncMock(side_effect=error)

    # Should return None, not raise exception
    result = await get_storage_document_by_event_id(
        client, engine_id=client.engine_id, event_id="event-123"
    )
    assert result is None


@pytest.mark.asyncio
async def test_list_storage_documents_single_page(mock_client):
    """Test listing storage documents with single page."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"EngineDocumentId": "doc-1", "Content": '{"food": "Apple"}'},
            {"EngineDocumentId": "doc-2", "Content": '{"food": "Banana"}'},
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 2,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id):
        results.append(doc)

    assert len(results) == 2
    assert results[0]["EngineDocumentId"] == "doc-1"


@pytest.mark.asyncio
async def test_list_storage_documents_multiple_pages(mock_client):
    """Test listing storage documents with pagination."""
    client, mock_http_client = mock_client

    # First page
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {
        "Items": [{"EngineDocumentId": "doc-1"}],
        "PageNumber": 1,
        "PageSize": 1,
        "TotalCount": 2,
        "TotalPages": 2,
    }

    # Second page
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {
        "Items": [{"EngineDocumentId": "doc-2"}],
        "PageNumber": 2,
        "PageSize": 1,
        "TotalCount": 2,
        "TotalPages": 2,
    }

    mock_http_client.get = AsyncMock(side_effect=[mock_response_1, mock_response_2])

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id, page_size=1):
        results.append(doc)

    assert len(results) == 2
    assert mock_http_client.get.call_count == 2


@pytest.mark.asyncio
async def test_get_storage_document_by_customer_key(mock_client):
    """Test getting storage documents by customer key."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [{"EngineDocumentId": "doc-1", "CustomerKey": "key-123"}],
        "PageNumber": 1,
        "PageSize": 25,
        "TotalCount": 1,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in get_storage_document_by_customer_key(
        client, engine_id=client.engine_id, customer_key="key-123"
    ):
        results.append(doc)

    assert len(results) == 1
    assert results[0]["CustomerKey"] == "key-123"


@pytest.mark.asyncio
async def test_query_storage_by_jsonpath(mock_client):
    """Test querying storage by JSONPath."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"EngineDocumentId": "doc-1", "Content": '{"meal_type": "breakfast"}'},
    ]
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in query_storage_by_jsonpath(
        client, engine_id=client.engine_id, json_path_query="$.meal_type:breakfast"
    ):
        results.append(doc)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_query_storage_by_jsonpath_not_found(mock_client):
    """Test querying storage by JSONPath when no matches."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in query_storage_by_jsonpath(
        client, engine_id=client.engine_id, json_path_query="$.nonexistent:value"
    ):
        results.append(doc)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_storage_methods_handle_errors_gracefully(mock_client):
    """Test storage methods handle errors gracefully."""
    client, mock_http_client = mock_client

    error = httpx.RequestError("Connection error")
    mock_http_client.get = AsyncMock(side_effect=error)

    # Should return empty iterable, not raise exception
    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id):
        results.append(doc)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_list_storage_documents_with_lowercase_keys(mock_client):
    """Test listing storage documents with lowercase response keys."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    # API returns lowercase keys (items, totalCount, totalPages)
    mock_response.json.return_value = {
        "items": [
            {"EngineDocumentId": "doc-1", "content": '{"food": "Apple"}'},
            {"EngineDocumentId": "doc-2", "content": '{"food": "Banana"}'},
        ],
        "pageNumber": 1,
        "pageSize": 100,
        "totalCount": 2,
        "totalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id):
        results.append(doc)

    assert len(results) == 2
    assert results[0]["EngineDocumentId"] == "doc-1"


@pytest.mark.asyncio
async def test_list_storage_documents_multiple_pages_lowercase_keys(mock_client):
    """Test pagination with lowercase response keys."""
    client, mock_http_client = mock_client

    # First page with lowercase keys
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {
        "items": [{"EngineDocumentId": "doc-1"}],
        "pageNumber": 1,
        "pageSize": 1,
        "totalCount": 2,
        "totalPages": 2,
    }

    # Second page with lowercase keys
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {
        "items": [{"EngineDocumentId": "doc-2"}],
        "pageNumber": 2,
        "pageSize": 1,
        "totalCount": 2,
        "totalPages": 2,
    }

    mock_http_client.get = AsyncMock(side_effect=[mock_response_1, mock_response_2])

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id, page_size=1):
        results.append(doc)

    assert len(results) == 2
    assert mock_http_client.get.call_count == 2


# High Priority Test Coverage Gaps


@pytest.mark.asyncio
async def test_query_storage_by_jsonpath_dict_response_lowercase_keys(mock_client):
    """Test query_storage_by_jsonpath with dict response and lowercase keys."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    # API returns dict with lowercase "items" key
    mock_response.json.return_value = {
        "items": [
            {"EngineDocumentId": "doc-1", "content": '{"meal_type": "breakfast"}'},
            {"EngineDocumentId": "doc-2", "content": '{"meal_type": "lunch"}'},
        ]
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in query_storage_by_jsonpath(
        client, engine_id=client.engine_id, json_path_query="$.meal_type:breakfast"
    ):
        results.append(doc)

    # Should return all items from the mock response (API filtering is mocked)
    assert len(results) == 2
    assert results[0]["EngineDocumentId"] == "doc-1"
    assert results[1]["EngineDocumentId"] == "doc-2"


@pytest.mark.asyncio
async def test_list_storage_documents_with_customer_key(mock_client):
    """Test list_storage_documents with customer_key parameter."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"EngineDocumentId": "doc-1", "CustomerKey": "key-123"},
            {"EngineDocumentId": "doc-2", "CustomerKey": "key-123"},
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 2,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(
        client, engine_id=client.engine_id, customer_key="key-123"
    ):
        results.append(doc)

    assert len(results) == 2
    # Verify that CustomerKey parameter was passed
    call_args = mock_http_client.get.call_args
    assert "CustomerKey" in call_args.kwargs["params"]
    assert call_args.kwargs["params"]["CustomerKey"] == "key-123"


@pytest.mark.asyncio
async def test_list_storage_documents_filter_rejects(mock_client):
    """Test list_storage_documents with filter function that filters out items."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"EngineDocumentId": "doc-1", "calories": 95},
            {"EngineDocumentId": "doc-2", "calories": 250},
            {"EngineDocumentId": "doc-3", "calories": 300},
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 3,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        # Only keep documents with calories > 200
        return doc.get("calories", 0) > 200

    results = []
    async for doc in list_storage_documents(
        client, engine_id=client.engine_id, filter_fn=filter_fn
    ):
        results.append(doc)

    # Should only return 2 items (doc-2 and doc-3), filtering out doc-1
    assert len(results) == 2
    assert all(doc.get("calories", 0) > 200 for doc in results)


@pytest.mark.asyncio
async def test_list_storage_documents_http_400_error(mock_client):
    """Test list_storage_documents handles HTTP 400 Bad Request."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id):
        results.append(doc)

    # Should return empty iterator on HTTP error (not raise exception)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_storage_document_by_customer_key_pagination_lowercase_keys(mock_client):
    """Test get_storage_document_by_customer_key pagination with lowercase keys."""
    client, mock_http_client = mock_client

    # First page with lowercase keys
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {
        "items": [{"EngineDocumentId": "doc-1", "CustomerKey": "key-123"}],
        "pageNumber": 1,
        "pageSize": 1,
        "totalCount": 2,
        "totalPages": 2,
    }

    # Second page with lowercase keys
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {
        "items": [{"EngineDocumentId": "doc-2", "CustomerKey": "key-123"}],
        "pageNumber": 2,
        "pageSize": 1,
        "totalCount": 2,
        "totalPages": 2,
    }

    mock_http_client.get = AsyncMock(side_effect=[mock_response_1, mock_response_2])

    results = []
    async for doc in get_storage_document_by_customer_key(
        client, engine_id=client.engine_id, customer_key="key-123", page_size=1
    ):
        results.append(doc)

    assert len(results) == 2
    assert mock_http_client.get.call_count == 2
    assert results[0]["CustomerKey"] == "key-123"
    assert results[1]["CustomerKey"] == "key-123"


# Tests for raw parameter functionality


@pytest.mark.asyncio
async def test_list_storage_documents_raw_true_returns_raw_dicts(mock_client):
    """Test list_storage_documents with raw=True returns raw dictionaries without deserialization."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple", "calories": 95}',
            },
            {
                "EngineDocumentId": "doc-2",
                "EventId": "event-2",
                "Content": '{"food_name": "Banana", "calories": 105}',
            },
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 2,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id, raw=True):
        results.append(doc)

    assert len(results) == 2
    # With raw=True, should return raw dicts with Content as JSON string, not deserialized
    assert isinstance(results[0], dict)
    assert "Content" in results[0]
    assert results[0]["Content"] == '{"food_name": "Apple", "calories": 95}'
    assert results[0]["EngineDocumentId"] == "doc-1"
    assert results[0]["EventId"] == "event-1"


@pytest.mark.asyncio
async def test_list_storage_documents_raw_false_deserializes(mock_client):
    """Test list_storage_documents with raw=False (default) deserializes items."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple", "calories": 95}',
            },
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 1,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id, raw=False):
        results.append(doc)

    assert len(results) == 1
    # With raw=False, Content field should be parsed (if model provided) or remain as dict
    assert isinstance(results[0], dict)
    # Without a model, it should return the raw dict structure
    assert "Content" in results[0] or "content" in results[0]


@pytest.mark.asyncio
async def test_list_storage_documents_raw_true_ignores_model(mock_client):
    """Test that raw=True ignores model parameter and returns raw dictionaries."""
    client, mock_http_client = mock_client

    # Create a simple model for testing
    from pydantic import BaseModel

    class FoodItem(BaseModel):
        food_name: str
        calories: int

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple", "calories": 95}',
            },
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 1,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(
        client, engine_id=client.engine_id, model=FoodItem, raw=True
    ):
        results.append(doc)

    assert len(results) == 1
    # With raw=True, should return raw dict even if model is provided
    assert isinstance(results[0], dict)
    assert not isinstance(results[0], FoodItem)
    assert "Content" in results[0]
    assert results[0]["Content"] == '{"food_name": "Apple", "calories": 95}'


@pytest.mark.asyncio
async def test_list_storage_documents_raw_true_with_filter(mock_client):
    """Test list_storage_documents with raw=True and filter function."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple", "calories": 95}',
            },
            {
                "EngineDocumentId": "doc-2",
                "EventId": "event-2",
                "Content": '{"food_name": "Banana", "calories": 105}',
            },
            {
                "EngineDocumentId": "doc-3",
                "EventId": "event-3",
                "Content": '{"food_name": "Orange", "calories": 62}',
            },
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 3,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        # Filter based on EventId in raw dict
        return doc.get("EventId") in ["event-1", "event-3"]

    results = []
    async for doc in list_storage_documents(
        client, engine_id=client.engine_id, raw=True, filter_fn=filter_fn
    ):
        results.append(doc)

    # Should return 2 items (event-1 and event-3), filtering out event-2
    assert len(results) == 2
    assert all(isinstance(doc, dict) for doc in results)
    event_ids = [doc["EventId"] for doc in results]
    assert "event-1" in event_ids
    assert "event-3" in event_ids
    assert "event-2" not in event_ids


@pytest.mark.asyncio
async def test_list_storage_documents_raw_true_pagination(mock_client):
    """Test list_storage_documents with raw=True handles pagination correctly."""
    client, mock_http_client = mock_client

    # First page
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple"}',
            }
        ],
        "PageNumber": 1,
        "PageSize": 1,
        "TotalCount": 2,
        "TotalPages": 2,
    }

    # Second page
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-2",
                "EventId": "event-2",
                "Content": '{"food_name": "Banana"}',
            }
        ],
        "PageNumber": 2,
        "PageSize": 1,
        "TotalCount": 2,
        "TotalPages": 2,
    }

    mock_http_client.get = AsyncMock(side_effect=[mock_response_1, mock_response_2])

    results = []
    async for doc in list_storage_documents(
        client, engine_id=client.engine_id, page_size=1, raw=True
    ):
        results.append(doc)

    assert len(results) == 2
    assert mock_http_client.get.call_count == 2
    # All results should be raw dicts
    assert all(isinstance(doc, dict) for doc in results)
    assert results[0]["EventId"] == "event-1"
    assert results[1]["EventId"] == "event-2"


@pytest.mark.asyncio
async def test_list_storage_documents_raw_true_lowercase_keys(mock_client):
    """Test list_storage_documents with raw=True handles lowercase response keys."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "content": '{"food_name": "Apple", "calories": 95}',
            },
        ],
        "pageNumber": 1,
        "pageSize": 100,
        "totalCount": 1,
        "totalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in list_storage_documents(client, engine_id=client.engine_id, raw=True):
        results.append(doc)

    assert len(results) == 1
    assert isinstance(results[0], dict)
    # Should preserve the lowercase "content" key from API response
    assert "content" in results[0] or "Content" in results[0]


@pytest.mark.asyncio
async def test_client_list_storage_documents_raw_true(mock_client):
    """Test client.list_storage_documents with raw=True."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {
                "EngineDocumentId": "doc-1",
                "EventId": "event-1",
                "Content": '{"food_name": "Apple", "calories": 95}',
            },
        ],
        "PageNumber": 1,
        "PageSize": 100,
        "TotalCount": 1,
        "TotalPages": 1,
    }
    mock_http_client.get = AsyncMock(return_value=mock_response)

    results = []
    async for doc in client.list_storage_documents(engine_id=client.engine_id, raw=True):
        results.append(doc)

    assert len(results) == 1
    assert isinstance(results[0], dict)
    assert "Content" in results[0]
    assert results[0]["Content"] == '{"food_name": "Apple", "calories": 95}'
