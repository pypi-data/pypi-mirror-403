"""Client for Rail Engine Ingestion."""

import json
import logging
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union, overload

import httpx
from pydantic import BaseModel

from railtown.engine.exceptions import (
    RailtownBadRequestError,
    RailtownError,
    RailtownServerError,
    RailtownUnauthorizedError,
)
from railtown.engine.ingest.auth import decode_engine_token, get_engine_token
from railtown.engine.ingest.models import (
    WebhookHandler,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class RailengineIngest(Generic[T]):
    """Client for ingesting data to Rail Engine."""

    def __init__(
        self,
        engine_token: Optional[str] = None,
        model: Optional[Type[T]] = None,
    ):
        """
        Initialize the RailengineIngest client.

        Args:
            engine_token: ENGINE_TOKEN (base64-encoded JSON). If not provided, reads from ENGINE_TOKEN environment variable.
            model: Optional Pydantic model type for validating ingested data. If provided, upsert() will validate data against this model.

        Raises:
            RailtownBadRequestError: If ENGINE_TOKEN is missing or invalid
        """
        # Get token from parameter or environment
        token = get_engine_token(engine_token)
        if not token:
            raise RailtownBadRequestError(
                "ENGINE_TOKEN is required. Provide it as a parameter or set ENGINE_TOKEN environment variable."
            )

        # Decode and validate token
        token_data = decode_engine_token(token)

        # Store properties (snake_case)
        self._ingestion_url = token_data["ingestion_url"]
        self._ingestion_api_token = token_data["ingestion_api_token"]
        self._engine_id = token_data["engine_id"]
        self._model: Optional[Type[T]] = model

        # Initialize HTTP client
        self._client = httpx.AsyncClient(verify=False, timeout=30.0)

        logger.info(f"Initialized RailengineIngest client for engine {self._engine_id}")

    @property
    def ingestion_url(self) -> str:
        """Get ingestion URL from decoded ENGINE_TOKEN."""
        return self._ingestion_url

    @property
    def ingestion_api_token(self) -> str:
        """Get ingestion API token from decoded ENGINE_TOKEN."""
        return self._ingestion_api_token

    @property
    def engine_id(self) -> str:
        """Get engine ID from decoded ENGINE_TOKEN."""
        return self._engine_id

    def _prepare_ingestion_url(self, url: str) -> str:
        """
        Prepare ingestion URL by adding protocol and path if needed.

        Args:
            url: Ingestion URL from token

        Returns:
            Prepared URL with protocol and path
        """
        # Remove whitespace
        url = url.strip()

        # Add protocol if missing
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        # Parse URL to check if it has a path
        # If URL ends with domain only (no path), add the default endpoint
        # If URL has a path but ends with /, append the endpoint
        # Otherwise, assume the URL is already complete

        # Check if URL has a path component (after domain)
        if "://" in url:
            parts = url.split("://", 1)
            if len(parts) == 2:
                domain_and_path = parts[1]
                # Check if there's a path after the domain
                if "/" in domain_and_path:
                    # Has a path - check if it ends with /
                    if domain_and_path.endswith("/"):
                        url = f"{url}api/Engine/Storage"
                    # Otherwise, assume URL is complete
                else:
                    # No path, just domain - add the endpoint
                    url = f"{url}/api/Engine/Storage"

        return url

    def _prepare_data(self, data: Union[T, BaseModel, Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Prepare data for ingestion, validating against model if provided.

        Args:
            data: Data to ingest (Pydantic model instance, dict, or JSON string)

        Returns:
            Dictionary ready for ingestion

        Raises:
            RailtownBadRequestError: If data validation fails
        """
        # Handle JSON string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise RailtownBadRequestError(f"Invalid JSON string: {str(e)}") from e

        # Handle Pydantic model instance
        if isinstance(data, BaseModel):
            data = data.model_dump()

        # Validate against model if provided
        if self._model:
            if not isinstance(data, dict):
                raise RailtownBadRequestError(
                    f"Data must be a dictionary for model validation. Got type: {type(data).__name__}"
                )
            try:
                # Create model instance to validate
                validated = self._model(**data)
                # Convert back to dict for serialization
                data = validated.model_dump()
            except Exception as e:
                raise RailtownBadRequestError(
                    f"Data validation failed against model {self._model.__name__}: {str(e)}"
                ) from e

        if not isinstance(data, dict):
            raise RailtownBadRequestError(
                f"Data must be a dictionary after validation. Got type: {type(data).__name__}"
            )

        return data

    @overload
    async def upsert(self, data: T) -> httpx.Response: ...

    @overload
    async def upsert(self, data: Dict[str, Any]) -> httpx.Response: ...

    @overload
    async def upsert(self, data: str) -> httpx.Response: ...

    async def upsert(self, data: Union[T, BaseModel, Dict[str, Any], str]) -> httpx.Response:
        """
        Upsert data to Rail Engine.

        The data is sent directly as JSON to the ingestion endpoint.

        Args:
            data: Data to ingest. Can be:
                - Pydantic model instance (if model type was provided during initialization)
                - Dictionary (will be validated against model if model type was provided)
                - JSON string (will be parsed and validated)

        Returns:
            HTTP response from the ingestion endpoint

        Raises:
            RailtownBadRequestError: If data validation fails
            RailtownUnauthorizedError: If authentication fails
            RailtownServerError: If server error occurs
            RailtownError: For other errors
        """
        # Prepare data (validate and convert to dict)
        data_dict = self._prepare_data(data)

        # The endpoint expects the user's data directly, not wrapped

        # Prepare URL
        endpoint = self._prepare_ingestion_url(self._ingestion_url)

        # Prepare headers
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "x-rail-auth": self._ingestion_api_token,
        }

        # Serialize data_dict directly to JSON (UTF-8)
        payload_json = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")

        logger.info(f"POSTing to ingestion endpoint: {endpoint}")
        logger.info(f"Payload: {payload_json.decode('utf-8')}")

        try:
            response = await self._client.post(
                endpoint,
                content=payload_json,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"Successfully ingested data. Status: {response.status_code}")
            return response
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text

            if status_code == 400:
                raise RailtownBadRequestError(
                    f"Bad request: {response_text}", status_code, response_text
                ) from e
            elif status_code == 401:
                raise RailtownUnauthorizedError(
                    f"Unauthorized: {response_text}", status_code, response_text
                ) from e
            elif status_code >= 500:
                raise RailtownServerError(
                    f"Server error: {response_text}", status_code, response_text
                ) from e
            else:
                raise RailtownError(
                    f"HTTP error {status_code}: {response_text}",
                    status_code,
                    response_text,
                ) from e
        except httpx.RequestError as e:
            raise RailtownError(f"Request error: {str(e)}") from e

    def get_webhook_handler(self) -> "WebhookHandler[T]":
        """
        Get a webhook handler configured with this client's model type.

        Returns:
            WebhookHandler instance configured with the client's model type (if provided during initialization)

        Raises:
            ValueError: If no model type was provided during client initialization
        """
        if not self._model:
            raise ValueError(
                "Model type is required for webhook handling. Initialize client with model parameter or provide model to WebhookHandler directly."
            )
        return WebhookHandler(model=self._model)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
