"""Data models for Rail Engine Ingestion SDK."""

import json
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class WebhookPublishingPayload(BaseModel):
    """Schema for engine webhook publishing payload."""

    EventId: str
    EngineId: str
    ProjectId: str
    CustomerKey: Optional[str] = None
    Body: str  # JSON stringified document
    # Additional fields may be included based on engine configuration

    def get_body_as(self, model: Type[T]) -> T:
        """
        Deserialize the Body field (JSON string) into a Pydantic model instance.

        Args:
            model: Pydantic model type to deserialize the Body into

        Returns:
            Instance of the provided model type

        Raises:
            ValidationError: If the JSON doesn't match the model schema
        """
        body_dict = json.loads(self.Body)
        return model(**body_dict)


class WebhookEvent(BaseModel, Generic[T]):
    """Wrapper class combining webhook payload metadata with deserialized body."""

    EventId: str
    EngineId: str
    ProjectId: str
    CustomerKey: Optional[str] = None
    body: T  # Deserialized body as Pydantic model instance


class WebhookHandler(Generic[T]):
    """Handler for parsing lists of webhook events."""

    def __init__(self, model: Optional[Type[T]] = None):
        """
        Initialize webhook handler.

        Args:
            model: Optional Pydantic model type for deserializing webhook bodies.
                   If provided, all events will be deserialized to this type.
        """
        self.model: Optional[Type[T]] = model

    def parse(self, payload: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[WebhookEvent[T]]:
        """
        Parse webhook payload into list of WebhookEvent objects.

        Args:
            payload: Either a list of webhook payload dictionaries or a single dictionary

        Returns:
            List of WebhookEvent objects, each containing payload metadata and deserialized body

        Raises:
            ValueError: If no model type is provided and payload needs deserialization
            ValidationError: If body JSON doesn't match the model schema
        """
        # Normalize to list
        if isinstance(payload, dict):
            payload = [payload]

        if not self.model:
            raise ValueError(
                "Model type is required for webhook parsing. Provide model during handler initialization or use get_webhook_handler() from client."
            )

        events = []
        for event_dict in payload:
            # Parse payload
            payload_obj = WebhookPublishingPayload(**event_dict)

            # Deserialize body
            body = payload_obj.get_body_as(self.model)

            # Create WebhookEvent
            event = WebhookEvent(
                EventId=payload_obj.EventId,
                EngineId=payload_obj.EngineId,
                ProjectId=payload_obj.ProjectId,
                CustomerKey=payload_obj.CustomerKey,
                body=body,
            )
            events.append(event)

        return events
