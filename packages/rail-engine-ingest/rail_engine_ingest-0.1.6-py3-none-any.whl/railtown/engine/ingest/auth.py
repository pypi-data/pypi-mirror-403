"""Authentication handling for Rail Engine Ingestion SDK."""

import base64
import json
import os
from typing import Dict, Optional

from railtown.engine.exceptions import RailtownBadRequestError


def get_engine_token(engine_token: Optional[str] = None) -> Optional[str]:
    """
    Get ENGINE_TOKEN from parameter or environment variable.

    Args:
        engine_token: ENGINE_TOKEN provided directly, or None to read from environment

    Returns:
        ENGINE_TOKEN string or None if not found
    """
    return engine_token or os.getenv("ENGINE_TOKEN")


def decode_engine_token(token: str) -> Dict[str, str]:
    """
    Decode and validate ENGINE_TOKEN.

    ENGINE_TOKEN is a base64-encoded JSON string containing:
    - IngestionUrl (PascalCase)
    - IngestionApiToken (PascalCase)
    - EngineId (PascalCase)

    Args:
        token: Base64-encoded JSON string

    Returns:
        Dictionary with decoded token data (snake_case keys)

    Raises:
        RailtownBadRequestError: If token is invalid, not base64, or missing required fields
    """
    if not token:
        raise RailtownBadRequestError("ENGINE_TOKEN is required but not provided")

    try:
        # Decode base64
        decoded_bytes = base64.b64decode(token)
        decoded_str = decoded_bytes.decode("utf-8")
    except Exception as e:
        raise RailtownBadRequestError(f"ENGINE_TOKEN is not valid base64: {str(e)}") from e

    try:
        # Parse JSON
        token_data = json.loads(decoded_str)
    except json.JSONDecodeError as e:
        raise RailtownBadRequestError(f"ENGINE_TOKEN does not contain valid JSON: {str(e)}") from e

    # Validate required fields (PascalCase from Platform)
    required_fields = ["IngestionUrl", "IngestionApiToken", "EngineId"]
    missing_fields = [field for field in required_fields if field not in token_data]

    if missing_fields:
        raise RailtownBadRequestError(
            f"ENGINE_TOKEN is missing required fields: {', '.join(missing_fields)}"
        )

    # Map PascalCase keys to snake_case properties
    return {
        "ingestion_url": token_data["IngestionUrl"],
        "ingestion_api_token": token_data["IngestionApiToken"],
        "engine_id": token_data["EngineId"],
    }
