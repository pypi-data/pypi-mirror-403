# Rail Engine Ingestion SDK

Python SDK for ingesting data into Railtown AI Rail Engine - handles embeddings, storage, indexing, and webhook publishing.

## Overview

The `rail-engine-ingest` package provides a Pythonic interface for publishing data to Rail Engine. It supports async/await patterns, Pydantic model validation, and familiar configuration patterns.

## Installation

```bash
uv pip install rail-engine-ingest
```

## Quick Start

```python

# Copy your ENGINE_TOKEN from https://cndr.railtown.ai Project Settings

import asyncio
from railtown.engine.ingest import RailengineIngest
import base64
import json

engine_token = os.getenv("ENGINE_TOKEN")

async def main():
    # Initialize client
    async with RailengineIngest(engine_token=engine_token) as client:
        # Ingest data
        data = {
            "name": "Chicken Shawarma",
            "meal": "lunch",
            "calories": 95
        }
        response = await client.upsert(data)
        print(f"Status: {response.status_code}")

asyncio.run(main())
```

## Configuration

### Environment Variable

- `ENGINE_TOKEN` - Base64-encoded JSON string containing ingestion credentials

### Constructor Parameters

- `engine_token` (optional) - ENGINE_TOKEN string (if not provided, reads from env)
- `model` (optional) - Pydantic model type for validating ingested data

## Features

- **Single `upsert()` method** - Unified interface for ingesting data
- **Multiple data formats** - Accepts Pydantic models, dictionaries, or JSON strings
- **Model validation** - Optional Pydantic model validation
- **Direct JSON payload** - Sends data directly as JSON to the ingestion endpoint
- **Async/await support** - Built for modern async Python applications

## Error Handling

The SDK provides custom exception classes:

- `RailtownError` - Base exception
- `RailtownBadRequestError` - 400 Bad Request
- `RailtownUnauthorizedError` - 401 Unauthorized
- `RailtownNotFoundError` - 404 Not Found
- `RailtownConflictError` - 409 Conflict
- `RailtownServerError` - 5xx Server errors

Exceptions are raised on errors.

## Requirements

- uv
- Python 3.10+
- httpx >= 0.24.0
- pydantic >= 1.10.0

## Related Package

For retrieving and searching data from Rail Engine, see [`rail-engine-ingest`](https://pypi.org/project/rail-engine-ingest/).

## License

MIT
