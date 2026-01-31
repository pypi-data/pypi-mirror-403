"""Storage API methods for Rail Engine."""

import logging
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from railtown.engine.utils import deserialize_item, filter_items

if TYPE_CHECKING:
    from railtown.engine.client import Railengine

logger = logging.getLogger(__name__)


async def get_storage_document_by_event_id(
    client: "Railengine",
    engine_id: Optional[str] = None,
    event_id: str = "",
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
) -> Optional[Any]:
    """
    Get a single storage document by EventId.

    Args:
        client: Railengine client instance
        engine_id: Engine ID (uses client.engine_id if not provided)
        event_id: EventId GUID
        filter_fn: Optional filter function that takes a document and returns bool
        model: Optional model type to override default model from client

    Returns:
        Document instance (deserialized to model type if provided) or None if not found
    """
    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    endpoint = f"{client.api_url}/api/Engine/{engine_id}/Storage"
    headers = client._get_headers()
    params = {"EventId": event_id}

    logger.info(f"Getting storage document by EventId: {event_id} (engine: {engine_id})")

    try:
        response = await client._client.get(endpoint, headers=headers, params=params, timeout=30.0)

        # Handle 404 as None (document not found)
        if response.status_code == 404:
            logger.info(f"Storage document not found: {event_id}")
            return None

        response.raise_for_status()

        result = response.json()

        # Deserialize
        deserialized = deserialize_item(result, default_model=client.model, override_model=model)

        # Apply filter if provided
        if filter_fn is not None and not filter_fn(deserialized):
            return None

        return deserialized

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        logger.error(
            f"HTTP error getting storage document: {e.response.status_code} - {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error getting storage document: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting storage document: {str(e)}", exc_info=True)
        return None


async def _paginated_storage_iterator(
    client: "Railengine",
    endpoint: str,
    params: Dict[str, Any],
    filter_fn: Optional[Callable[[Any], bool]] = None,
    default_model: Optional[Type[BaseModel]] = None,
    override_model: Optional[Type[BaseModel]] = None,
    raw: bool = False,
) -> AsyncIterator[Any]:
    """
    Internal helper to iterate through paginated storage results.

    Args:
        client: Railengine client instance
        endpoint: API endpoint URL
        params: Query parameters (will be updated with pagination)
        filter_fn: Optional filter function
        default_model: Default model type from client
        override_model: Override model type
        raw: If True, return raw response dictionaries without deserialization

    Yields:
        Storage documents (deserialized and filtered, or raw dicts if raw=True)
    """
    headers = client._get_headers()
    # Ensure page_number and page_size are integers
    page_number = int(params.get("PageNumber", 1))
    page_size = int(params.get("PageSize", 100))

    while True:
        # Update params with current page
        current_params = {
            **params,
            "PageNumber": str(page_number),
            "PageSize": str(page_size),
        }

        try:
            response = await client._client.get(
                endpoint, headers=headers, params=current_params, timeout=30.0
            )

            # Handle 404 as empty result
            if response.status_code == 404:
                logger.info("No more pages (404)")
                break

            response.raise_for_status()
            result = response.json()

            # Handle both dict and list responses
            if isinstance(result, list):
                items = result
                total_pages = 1
                total_count = len(items)
            else:
                # API returns lowercase "items" but we check both for compatibility
                items = result.get("items", result.get("Items", []))
                total_pages = int(result.get("TotalPages", result.get("totalPages", 1)))
                total_count = int(result.get("TotalCount", result.get("totalCount", 0)))

            # If no items, break
            if not items:
                break

            # Filter and deserialize items
            for item in items:
                if raw:
                    # Return raw item without deserialization
                    if filter_fn is None or filter_fn(item):
                        yield item
                else:
                    # Deserialize item
                    deserialized = deserialize_item(
                        item, default_model=default_model, override_model=override_model
                    )
                    if filter_fn is None or filter_fn(deserialized):
                        yield deserialized

            # Check if we've reached the last page
            if page_number >= total_pages:
                break

            page_number += 1

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # 404 means no more pages
                break
            logger.error(
                f"HTTP error in paginated request: {e.response.status_code} - {e.response.text}"
            )
            break
        except httpx.RequestError as e:
            logger.error(f"Request error in paginated request: {str(e)}")
            break
        except Exception as e:
            logger.error(f"Error in paginated request: {str(e)}", exc_info=True)
            break


async def get_storage_document_by_customer_key(
    client: "Railengine",
    engine_id: Optional[str] = None,
    customer_key: str = "",
    page_number: int = 1,
    page_size: int = 25,
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
) -> AsyncIterator[Any]:
    """
    Get storage documents by CustomerKey.

    Returns all versions of documents with the given CustomerKey, handling pagination automatically.

    Args:
        client: Railengine client instance
        engine_id: Engine ID (uses client.engine_id if not provided)
        customer_key: CustomerKey string
        page_number: Starting page number (default: 1)
        page_size: Page size (default: 25, max: 100)
        filter_fn: Optional filter function that takes an item and returns bool
        model: Optional model type to override default model from client

    Yields:
        Storage documents (deserialized to model type if provided, paginated results are automatically flattened)
    """
    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    endpoint = f"{client.api_url}/api/Engine/{engine_id}/Storage"
    params = {
        "CustomerKey": customer_key,
        "PageNumber": str(page_number),
        "PageSize": str(min(page_size, 100)),  # Cap at 100
    }

    logger.info(f"Getting storage documents by CustomerKey: {customer_key} (engine: {engine_id})")

    async for item in _paginated_storage_iterator(
        client, endpoint, params, filter_fn, client.model, model
    ):
        yield item


async def query_storage_by_jsonpath(
    client: "Railengine",
    engine_id: Optional[str] = None,
    json_path_query: str = "",
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
) -> AsyncIterator[Any]:
    """
    Query storage by JSONPath.

    Args:
        client: Railengine client instance
        engine_id: Engine ID (uses client.engine_id if not provided)
        json_path_query: JSONPath query string (e.g., "$.direct_report_id:1")
        filter_fn: Optional filter function that takes an item and returns bool
        model: Optional model type to override default model from client

    Yields:
        Matching storage documents (deserialized to model type if provided)
    """
    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    endpoint = f"{client.api_url}/api/Engine/{engine_id}/Storage"
    headers = client._get_headers()
    params = {"JsonPathQuery": json_path_query}

    logger.info(f"Querying storage by JSONPath: {json_path_query} (engine: {engine_id})")

    try:
        response = await client._client.get(endpoint, headers=headers, params=params, timeout=30.0)

        # Handle 404 as empty result
        if response.status_code == 404:
            logger.info(f"No matches found for JSONPath query: {json_path_query}")
            return

        response.raise_for_status()
        result = response.json()

        # Handle both list and dict responses
        if isinstance(result, list):
            items = result
        else:
            # API returns lowercase "items" but we check both for compatibility
            items = result.get("items", result.get("Items", []))

        # Filter and deserialize items
        async for item in filter_items(
            iter(items),
            filter_fn=filter_fn,
            default_model=client.model,
            override_model=model,
        ):
            yield item

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 means no matches, return empty iterator
            return
        logger.error(
            f"HTTP error querying storage by JSONPath: {e.response.status_code} - {e.response.text}"
        )
        return
    except httpx.RequestError as e:
        logger.error(f"Request error querying storage by JSONPath: {str(e)}")
        return
    except Exception as e:
        logger.error(f"Error querying storage by JSONPath: {str(e)}", exc_info=True)
        return


async def list_storage_documents(
    client: "Railengine",
    engine_id: Optional[str] = None,
    customer_key: Optional[str] = None,
    page_number: int = 1,
    page_size: int = 100,
    filter_fn: Optional[Callable[[Any], bool]] = None,
    model: Optional[Type[BaseModel]] = None,
    raw: bool = False,
) -> AsyncIterator[Any]:
    """
    List storage documents.

    Handles pagination automatically, fetching all pages and yielding items one by one.

    Args:
        client: Railengine client instance
        engine_id: Engine ID (uses client.engine_id if not provided)
        customer_key: Optional CustomerKey filter
        page_number: Starting page number (default: 1)
        page_size: Page size (default: 100, max: 100)
        filter_fn: Optional filter function that takes an item and returns bool
        model: Optional model type to override default model from client
        raw: If True, return raw response dictionaries without deserialization to model

    Yields:
        Storage documents (deserialized to model type if provided, or raw dicts if raw=True,
        paginated results are automatically flattened)
    """
    # Use client's engine_id if not provided
    engine_id = engine_id or client.engine_id

    endpoint = f"{client.api_url}/api/Engine/{engine_id}/Storage"
    params = {
        "PageNumber": str(page_number),
        "PageSize": str(min(page_size, 100)),  # Cap at 100
    }

    if customer_key:
        params["CustomerKey"] = customer_key

    logger.info(f"Listing storage documents (engine: {engine_id})")

    async for item in _paginated_storage_iterator(
        client, endpoint, params, filter_fn, client.model, model, raw
    ):
        yield item
