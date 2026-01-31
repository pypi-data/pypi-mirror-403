"""Client for Rail Engine Retrieval."""

import logging
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)

import httpx
from pydantic import BaseModel

from railtown.engine.auth import get_api_url, get_engine_id, get_pat, normalize_base_url
from railtown.engine.embeddings import search_vector_store
from railtown.engine.exceptions import (
    RailtownBadRequestError,
    RailtownError,
    RailtownNotFoundError,
    RailtownServerError,
    RailtownUnauthorizedError,
)
from railtown.engine.indexing import search_index
from railtown.engine.storage import (
    get_storage_document_by_customer_key,
    get_storage_document_by_event_id,
    list_storage_documents,
    query_storage_by_jsonpath,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Railengine(Generic[T]):
    """Client for retrieving data from Rail Engine."""

    def __init__(
        self,
        pat: Optional[str] = None,
        engine_id: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[Type[T]] = None,
    ):
        """
        Initialize the Railengine client.

        Args:
            pat: PAT token. If not provided, reads from ENGINE_PAT environment variable.
            engine_id: Engine ID. If not provided, reads from ENGINE_ID environment variable.
                      Required if not in environment.
            api_url: Base API URL. If not provided, reads from RAILTOWN_API_URL environment variable
                     or defaults to production (https://cndr.railtown.ai/api).
            model: Optional Pydantic model type for deserializing retrieved data.
                   If provided, retrieval methods will return instances of this type by default.

        Raises:
            RailtownBadRequestError: If required parameters are missing
        """
        # Get PAT from parameter or environment
        self._pat = get_pat(pat)
        if not self._pat:
            raise RailtownBadRequestError(
                "PAT is required. Provide it as a parameter or set ENGINE_PAT environment variable."
            )

        # Get engine_id from parameter or environment
        self._engine_id = get_engine_id(engine_id)
        if not self._engine_id:
            raise RailtownBadRequestError(
                "engine_id is required. Provide it as a parameter or set ENGINE_ID environment variable."
            )

        # Get API URL from parameter or environment
        raw_api_url = get_api_url(api_url)
        # Normalize base URL (strip /api suffix if present)
        self._api_url = normalize_base_url(raw_api_url)

        # Store model type
        self._model: Optional[Type[T]] = model

        # Initialize HTTP client
        self._client = httpx.AsyncClient(verify=False, timeout=30.0)

        logger.info(f"Initialized Railengine client for engine {self._engine_id}")

    @property
    def pat(self) -> str:
        """Get PAT token."""
        assert self._pat is not None  # Checked in __init__
        return self._pat

    @property
    def engine_id(self) -> str:
        """Get engine ID."""
        assert self._engine_id is not None  # Checked in __init__
        return self._engine_id

    @property
    def api_url(self) -> str:
        """Get base API URL."""
        return self._api_url

    @property
    def model(self) -> Optional[Type[T]]:
        """Get default model type."""
        return self._model

    def _get_headers(self) -> dict:
        """
        Get default headers for API requests.

        Returns:
            Dictionary with Authorization header
        """
        return {
            "Authorization": self._pat,
            "Content-Type": "application/json; charset=utf-8",
        }

    # Add convenience methods that delegate to module functions
    async def search_vector_store(
        self,
        engine_id: Optional[str] = None,
        vector_store: Literal["VectorStore1", "VectorStore2", "VectorStore3"] = "VectorStore1",
        query: str = "",
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
    ) -> AsyncIterator[Union[T, Dict[str, Any]]]:
        """
        Search a vector store using semantic search.

        Args:
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.
            vector_store: Vector store name. Must be one of: "VectorStore1", "VectorStore2", "VectorStore3".
                        Defaults to "VectorStore1".
            query: Query string for semantic search. This will be used to find similar embeddings.
            filter_fn: Optional filter function that takes an item and returns bool. Results will be
                      filtered client-side using this function.
            model: Optional Pydantic model type to override the default model from client initialization.
                   If provided, results will be deserialized to this model type instead of the default.

        Yields:
            Search results. If a model type is provided (either from client initialization or this method),
            results will be instances of that model. Otherwise, results will be dictionaries.

        Example:
            ```python
            # Basic search
            async for item in client.search_vector_store(
                vector_store="VectorStore1",
                query="healthy breakfast"
            ):
                print(item)

            # Search with filtering
            async for item in client.search_vector_store(
                vector_store="VectorStore2",
                query="high protein",
                filter_fn=lambda x: x.calories > 200
            ):
                print(item)
            ```
        """
        async for item in search_vector_store(
            self, engine_id, vector_store, query, filter_fn, model
        ):
            yield item

    async def get_storage_document_by_event_id(
        self,
        engine_id: Optional[str] = None,
        event_id: str = "",
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
    ) -> Optional[Union[T, Dict[str, Any]]]:
        """
        Get a single storage document by EventId.

        Retrieves a storage document from the Rail Engine storage API using its EventId.
        Returns None if the document is not found or if the filter function excludes it.

        Args:
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.
            event_id: EventId GUID of the document to retrieve.
            filter_fn: Optional filter function that takes a document and returns bool. Results will be
                      filtered client-side using this function. If the filter returns False, None is returned.
            model: Optional Pydantic model type to override the default model from client initialization.
                   If provided, the document will be deserialized to this model type instead of the default.

        Returns:
            The document as an instance of the model type (if a model is provided), a dictionary (if no model),
            or None if the document is not found or is filtered out.

        Example:
            ```python
            # Basic retrieval
            doc = await client.get_storage_document_by_event_id(
                event_id="123e4567-e89b-12d3-a456-426614174000"
            )
            if doc:
                print(doc)

            # With filtering
            doc = await client.get_storage_document_by_event_id(
                event_id="123e4567-e89b-12d3-a456-426614174000",
                filter_fn=lambda x: x.get("status") == "active"
            )

            # With model override
            from pydantic import BaseModel
            class MyModel(BaseModel):
                name: str
                value: int

            doc = await client.get_storage_document_by_event_id(
                event_id="123e4567-e89b-12d3-a456-426614174000",
                model=MyModel
            )
            ```
        """
        return await get_storage_document_by_event_id(self, engine_id, event_id, filter_fn, model)

    async def get_storage_document_by_customer_key(
        self,
        engine_id: Optional[str] = None,
        customer_key: str = "",
        page_number: int = 1,
        page_size: int = 25,
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
    ) -> AsyncIterator[Union[T, Dict[str, Any]]]:
        """Get storage documents by CustomerKey. See railtown.engine.storage.get_storage_document_by_customer_key for details."""
        async for item in get_storage_document_by_customer_key(
            self, engine_id, customer_key, page_number, page_size, filter_fn, model
        ):
            yield item

    async def query_storage_by_jsonpath(
        self,
        engine_id: Optional[str] = None,
        json_path_query: str = "",
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
    ) -> AsyncIterator[Union[T, Dict[str, Any]]]:
        """
        Query storage documents using a JSONPath query.

        Searches storage documents using a JSONPath query string to find documents matching
        specific criteria. Returns an empty iterator if no matches are found or if an error occurs.

        Args:
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.
            json_path_query: JSONPath query string used to filter documents. Examples:
                           - "$.meal_type:breakfast" - Find documents where meal_type equals "breakfast"
                           - "$.direct_report_id:1" - Find documents where direct_report_id equals 1
                           The query follows JSONPath syntax with value matching.
            filter_fn: Optional filter function that takes an item and returns bool. Results will be
                      filtered client-side using this function.
            model: Optional Pydantic model type to override the default model from client initialization.
                   If provided, documents will be deserialized to this model type instead of the default.

        Yields:
            Matching storage documents. If a model type is provided (either from client initialization or this method),
            results will be instances of that model. Otherwise, results will be dictionaries.
            Returns an empty iterator if no matches are found or if an error occurs.

        """
        async for item in query_storage_by_jsonpath(
            self, engine_id, json_path_query, filter_fn, model
        ):
            yield item

    async def list_storage_documents(
        self,
        engine_id: Optional[str] = None,
        customer_key: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 100,
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
        raw: bool = False,
    ) -> AsyncIterator[Union[T, Dict[str, Any]]]:
        """
        List storage documents with automatic pagination.

        Retrieves storage documents from the Rail Engine storage API. Pagination is handled
        automatically, fetching all pages and yielding items one by one. Optionally filters
        documents by CustomerKey.

        Args:
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.
            customer_key: Optional CustomerKey filter. If provided, only documents with this
                        CustomerKey will be returned.
            page_number: Starting page number (default: 1). Used to control where pagination starts.
            page_size: Page size (default: 100, max: 100). Maximum number of items per page.
                     Values greater than 100 will be capped at 100.
            filter_fn: Optional filter function that takes an item and returns bool. Results will be
                      filtered client-side using this function.
            model: Optional Pydantic model type to override the default model from client initialization.
                   If provided, documents will be deserialized to this model type instead of the default.
            raw: If True, return raw response dictionaries without deserialization to model.
                 When raw=True, the model parameter is ignored and items are returned as dictionaries.

        Yields:
            Storage documents. If raw=True, results will be raw dictionaries from the API response.
            Otherwise, if a model type is provided (either from client initialization or this method),
            results will be instances of that model. If no model and raw=False, results will be dictionaries.
            Paginated results are automatically flattened, so you'll receive all documents across all pages
            as a single stream.

        Example:
            ```python
            # List all documents
            async for doc in client.list_storage_documents():
                print(doc)

            # List documents with CustomerKey filter
            async for doc in client.list_storage_documents(
                customer_key="food-diary-123"
            ):
                print(doc)

            # List with pagination control
            async for doc in client.list_storage_documents(
                page_number=1,
                page_size=50
            ):
                print(doc)

            # List with client-side filtering
            async for doc in client.list_storage_documents(
                filter_fn=lambda x: x.get("status") == "active"
            ):
                print(doc)

            # List with model override
            from pydantic import BaseModel
            class MyDocument(BaseModel):
                name: str
                value: int

            async for doc in client.list_storage_documents(
                customer_key="my-key",
                model=MyDocument
            ):
                print(doc.name)

            # List with raw response (no deserialization)
            async for doc in client.list_storage_documents(raw=True):
                print(doc)  # doc is a raw dict from the API
            ```
        """
        async for item in list_storage_documents(
            self, engine_id, customer_key, page_number, page_size, filter_fn, model, raw
        ):
            yield item

    async def search_index(
        self,
        project_id: str = "",
        engine_id: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
        filter_fn: Optional[Callable[[Any], bool]] = None,
        model: Optional[Type[BaseModel]] = None,
    ) -> AsyncIterator[Union[T, Dict[str, Any]]]:
        """
        Search index using the Railtown indexing API.

        Performs a search query against the Rail Engine index for a specific project.
        The query is sent as a POST request with a dictionary containing search parameters.
        Returns an empty iterator if project_id is not provided or if an error occurs.

        Args:
            project_id: Project ID (required). The search will not execute if this is empty.
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.
            query: Optional query dictionary containing search parameters. Common keys include:
                  - "search": Search query string (e.g., {"search": "apple"})
                  - "filter": Additional filter criteria
                  If None, an empty dictionary is sent.
            filter_fn: Optional filter function that takes an item and returns bool. Results will be
                      filtered client-side using this function.
            model: Optional Pydantic model type to override the default model from client initialization.
                   If provided, results will be deserialized to this model type instead of the default.

        Yields:
            Search results. If a model type is provided (either from client initialization or this method),
            results will be instances of that model. Otherwise, results will be dictionaries.
            Returns an empty iterator if project_id is missing or if an error occurs.

        Example:
            ```python
            # Basic search
            async for item in client.search_index(
                project_id="your-project-id",
                query={"search": "apple"}
            ):
                print(item)

            # Search with filtering
            async for item in client.search_index(
                project_id="your-project-id",
                query={"search": "breakfast", "filter": "meal_type:morning"},
                filter_fn=lambda x: x.get("calories", 0) > 200
            ):
                print(item)

            # Search with model override
            from pydantic import BaseModel
            class SearchResult(BaseModel):
                title: str
                content: str

            async for item in client.search_index(
                project_id="your-project-id",
                query={"search": "healthy recipes"},
                model=SearchResult
            ):
                print(item.title)
            ```
        """
        async for item in search_index(self, project_id, engine_id, query, filter_fn, model):
            yield item

    async def delete_event(
        self,
        event_id: str,
        engine_id: Optional[str] = None,
    ) -> httpx.Response:
        """
        Delete an event from the Rail Engine.

        Deletes an event from hot storage, embeddings, and indexing systems.
        The operation is idempotent - calling delete multiple times on the same event
        will have the same result.

        Args:
            event_id: EventId GUID of the event to delete (required).
            engine_id: Engine ID. If not provided, uses the engine_id from client initialization.

        Returns:
            httpx.Response: HTTP response object from the API.
            - Status 204: Event was deleted immediately or was already deleted (idempotent success).
            - Status 202: Event data is marked for deletion, but it may take some time
                         (index deletes are eventually consistent).

        Raises:
            RailtownBadRequestError: If event_id is empty or invalid (400).
            RailtownUnauthorizedError: If authentication fails (401).
            RailtownNotFoundError: If engine is not found (404).
            RailtownServerError: If server error occurs (503 or other 5xx).
            RailtownError: For other HTTP errors.

        Example:
            ```python
            # Delete an event
            try:
                response = await client.delete_event(event_id="123e4567-e89b-12d3-a456-426614174000")
                if response.status_code == 204:
                    print("Event deleted immediately")
                elif response.status_code == 202:
                    print("Event deletion accepted, may take some time")
            except RailtownNotFoundError:
                print("Engine not found")
            except RailtownServerError as e:
                print(f"Server error: {e.message}")
            ```
        """
        # Validate event_id
        if not event_id:
            raise RailtownBadRequestError("event_id is required and cannot be empty")

        # Use client's engine_id if not provided
        target_engine_id = engine_id or self._engine_id

        # Build endpoint URL
        endpoint = f"{self._api_url}/api/Engine/{target_engine_id}/Event/{event_id}"
        headers = self._get_headers()

        logger.info(f"Deleting event: {event_id} (engine: {target_engine_id})")

        try:
            response = await self._client.delete(endpoint, headers=headers, timeout=30.0)

            # Handle success cases (204 and 202)
            if response.status_code in (204, 202):
                logger.info(
                    f"Event deletion {'completed' if response.status_code == 204 else 'accepted'}: {event_id}"
                )
                return response

            # Handle error cases
            if response.status_code == 404:
                raise RailtownNotFoundError(
                    f"Engine not found: {target_engine_id}",
                    status_code=404,
                    response_text=response.text,
                )
            elif response.status_code == 401:
                raise RailtownUnauthorizedError(
                    f"Unauthorized: {response.text}",
                    status_code=401,
                    response_text=response.text,
                )
            elif response.status_code == 400:
                raise RailtownBadRequestError(
                    f"Bad request: {response.text}",
                    status_code=400,
                    response_text=response.text,
                )
            elif response.status_code == 503 or response.status_code >= 500:
                raise RailtownServerError(
                    f"Server error: {response.text}",
                    status_code=response.status_code,
                    response_text=response.text,
                )
            else:
                # Other 4xx errors
                raise RailtownError(
                    f"HTTP error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                    response_text=response.text,
                )

        except (
            RailtownBadRequestError,
            RailtownUnauthorizedError,
            RailtownNotFoundError,
            RailtownServerError,
            RailtownError,
        ):
            # Re-raise our custom exceptions
            raise
        except httpx.HTTPStatusError as e:
            # Handle httpx exceptions and convert to our custom exceptions
            status_code = e.response.status_code
            response_text = e.response.text

            if status_code == 404:
                raise RailtownNotFoundError(
                    f"Engine not found: {target_engine_id}",
                    status_code=status_code,
                    response_text=response_text,
                ) from e
            elif status_code == 401:
                raise RailtownUnauthorizedError(
                    f"Unauthorized: {response_text}",
                    status_code=status_code,
                    response_text=response_text,
                ) from e
            elif status_code == 400:
                raise RailtownBadRequestError(
                    f"Bad request: {response_text}",
                    status_code=status_code,
                    response_text=response_text,
                ) from e
            elif status_code == 503 or status_code >= 500:
                raise RailtownServerError(
                    f"Server error: {response_text}",
                    status_code=status_code,
                    response_text=response_text,
                ) from e
            else:
                raise RailtownError(
                    f"HTTP error {status_code}: {response_text}",
                    status_code=status_code,
                    response_text=response_text,
                ) from e
        except httpx.RequestError as e:
            raise RailtownError(f"Request error: {str(e)}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
