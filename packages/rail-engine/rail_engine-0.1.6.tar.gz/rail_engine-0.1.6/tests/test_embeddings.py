"""Tests for embeddings API methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from railtown.engine.client import Railengine
from railtown.engine.embeddings import search_vector_store


@pytest.fixture
def mock_client(sample_pat, sample_engine_id):
    """Create a mock Railengine client."""
    with patch("railtown.engine.embeddings.httpx.AsyncClient") as mock_client_class:
        mock_http_client = AsyncMock()
        mock_client_class.return_value = mock_http_client

        client = Railengine(pat=sample_pat, engine_id=sample_engine_id)
        client._client = mock_http_client
        yield client, mock_http_client


@pytest.mark.asyncio
async def test_search_vector_store_success(mock_client):
    """Test searching vector store successfully."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"EventId": "event-1", "Embeddings": [0.1, 0.2, 0.3]},
            {"EventId": "event-2", "Embeddings": [0.4, 0.5, 0.6]},
        ]
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)

    results = []
    async for item in search_vector_store(
        client,
        engine_id=client.engine_id,
        vector_store="VectorStore1",
        query="apple",
    ):
        results.append(item)

    assert len(results) == 2
    assert results[0]["EventId"] == "event-1"
    mock_http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_search_vector_store_with_filter(mock_client):
    """Test searching vector store with filter function."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"EventId": "event-1", "VectorStore": "VectorStore1"},
            {"EventId": "event-2", "VectorStore": "VectorStore2"},
        ]
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)

    def filter_fn(item):
        return item.get("VectorStore") == "VectorStore1"

    results = []
    async for item in search_vector_store(
        client,
        engine_id=client.engine_id,
        vector_store="VectorStore1",
        query="test",
        filter_fn=filter_fn,
    ):
        results.append(item)

    assert len(results) == 1
    assert results[0]["EventId"] == "event-1"


@pytest.mark.asyncio
async def test_search_vector_store_empty_results(mock_client):
    """Test searching vector store with empty results."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Items": []}
    mock_http_client.post = AsyncMock(return_value=mock_response)

    results = []
    async for item in search_vector_store(
        client,
        engine_id=client.engine_id,
        vector_store="VectorStore1",
        query="nonexistent",
    ):
        results.append(item)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_vector_store_handles_errors_gracefully(mock_client):
    """Test search_vector_store handles errors gracefully."""
    client, mock_http_client = mock_client

    error = httpx.HTTPStatusError("Server Error", request=MagicMock(), response=MagicMock())
    mock_http_client.post = AsyncMock(side_effect=error)

    results = []
    async for item in search_vector_store(
        client,
        engine_id=client.engine_id,
        vector_store="VectorStore1",
        query="test",
    ):
        results.append(item)

    # Should return empty iterable on error
    assert len(results) == 0
