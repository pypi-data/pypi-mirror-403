# Rail Engine Python SDK

Python SDK for Railtown AI Rail Engine - providing a Pythonic interface for ingesting and retrieving data from Rail Engine.

## Overview

The Rail Engine Python SDK is split into two separate packages:

- **`rail-engine-ingest`** - For publishing data to Rail Engine (handles embeddings, storage, indexing, and webhook publishing)
- **`rail-engine`** - For retrieving and searching data (embeddings, storage documents, and indexed content)

Both packages support:

- Async/await patterns
- Client-side filtering
- Automatic pagination
- Pydantic model support for type safety
- Familiar configuration patterns (like OpenAI SDK)

## Installation

### Ingestion Package

```bash
uv pip install rail-engine-ingest
```

### Retrieval Package

```bash
uv pip install rail-engine
```

### Both Packages

```bash
uv pip install rail-engine-ingest rail-engine
```

## Quick Start

### Ingestion

```python
import asyncio
from railtown.engine.ingest import RailengineIngest
import base64
import json

# Create ENGINE_TOKEN (base64-encoded JSON)
token_data = {
    "IngestionUrl": "https://eng123.railtownlogs.com",
    "IngestionApiToken": "your-auth-token",
    "EngineId": "your-engine-guid"
}
engine_token = base64.b64encode(json.dumps(token_data).encode()).decode()

async def main():
    # Initialize client
    async with RailengineIngest(engine_token=engine_token) as client:
        # Ingest data
        data = {
            "EventId": "event-123",
            "ProjectId": "project-456",
            "food_name": "Apple",
            "calories": 95
        }
        response = await client.upsert(data)
        print(f"Status: {response.status_code}")

asyncio.run(main())
```

### Retrieval

```python
import asyncio
from railtown.engine import Railengine

async def main():
    # Initialize client (reads from ENGINE_PAT and ENGINE_ID env vars)
    async with Railengine() as client:
        # Search vector store
        results = client.search_vector_store(
            engine_id=client.engine_id,
            vector_store="VectorStore1",
            query="apple"
        )
        async for item in results:
            print(item)

asyncio.run(main())
```

## Configuration

### Ingestion (`rail-engine-ingest`)

**Environment Variable:**

- `ENGINE_TOKEN` - Base64-encoded JSON string containing ingestion credentials

**Constructor Parameters:**

- `engine_token` (optional) - ENGINE_TOKEN string (if not provided, reads from env)
- `model` (optional) - Pydantic model type for validating ingested data

### Retrieval (`rail-engine`)

**Environment Variables:**

- `ENGINE_PAT` (required) - Personal Access Token
- `ENGINE_ID` (required) - Engine ID (can also be passed to constructor)
- `RAILTOWN_API_URL` (optional) - Base API URL (defaults to `https://cndr.railtown.ai/api`)

**Constructor Parameters:**

- `pat` (optional) - PAT token (if not provided, reads from `ENGINE_PAT` env)
- `engine_id` (optional) - Engine ID (if not provided, reads from `ENGINE_ID` env, required if not in env)
- `api_url` (optional) - Base API URL (if not provided, reads from `RAILTOWN_API_URL` env or defaults to production)
- `model` (optional) - Pydantic model type for deserializing retrieved data

## Features

### Ingestion Features

- **Single `upsert()` method** - Unified interface for ingesting data
- **Multiple data formats** - Accepts Pydantic models, dictionaries, or JSON strings
- **Model validation** - Optional Pydantic model validation
- **Direct JSON payload** - Sends data directly as JSON to the ingestion endpoint
- **UTF-8 encoding** - All text operations use UTF-8

### Retrieval Features

- **Multiple retrieval methods**:
  - `search_vector_store()` - Semantic search in vector stores
  - `get_storage_document_by_event_id()` - Get document by EventId
  - `get_storage_document_by_customer_key()` - Get documents by customer key
  - `query_storage_by_jsonpath()` - Query using JSONPath
  - `list_storage_documents()` - List all documents with pagination
  - `search_index()` - Full-text search using Azure Search
- **Client-side filtering** - Filter results using `filter_fn` parameter
- **Automatic pagination** - Handles pagination automatically
- **Model deserialization** - Optional Pydantic model support with per-call override
- **Graceful error handling** - Returns None or empty iterables on errors

## Examples

See the [`samples/`](samples/) directory for comprehensive examples:

- [`samples/ingestion_example.py`](samples/ingestion_example.py) - Ingestion examples
- [`samples/retrieval_example.py`](samples/retrieval_example.py) - Retrieval examples
- [`samples/README.md`](samples/README.md) - Samples documentation

## API Reference

### Ingestion Client (`RailengineIngest`)

#### Methods

- `upsert(data)` - Upsert data to Rail Engine
  - Accepts: Pydantic model instance, dict, or JSON string
  - Returns: HTTP response

#### Properties

- `ingestion_url` - Ingestion URL from decoded ENGINE_TOKEN
- `ingestion_api_token` - API token from decoded ENGINE_TOKEN
- `engine_id` - Engine ID from decoded ENGINE_TOKEN

### Retrieval Client (`Railengine`)

#### Methods

- `search_vector_store(engine_id, vector_store, query, filter_fn=None, model=None)` - Search vector store
- `get_storage_document_by_event_id(engine_id, event_id, filter_fn=None, model=None)` - Get document by EventId
- `get_storage_document_by_customer_key(engine_id, customer_key, page_number=1, page_size=25, filter_fn=None, model=None)` - Get documents by customer key
- `query_storage_by_jsonpath(engine_id, json_path_query, filter_fn=None, model=None)` - Query by JSONPath
- `list_storage_documents(engine_id, customer_key=None, page_number=1, page_size=100, filter_fn=None, model=None)` - List documents
- `search_index(project_id, engine_id, query, filter_fn=None, model=None)` - Search index

#### Properties

- `pat` - PAT token
- `engine_id` - Engine ID
- `api_url` - Base API URL
- `model` - Default model type

## Error Handling

The SDK provides custom exception classes:

- `RailtownError` - Base exception
- `RailtownBadRequestError` - 400 Bad Request
- `RailtownUnauthorizedError` - 401 Unauthorized
- `RailtownNotFoundError` - 404 Not Found
- `RailtownConflictError` - 409 Conflict
- `RailtownServerError` - 5xx Server errors

**Ingestion**: Raises exceptions on errors
**Retrieval**: Returns `None` or empty iterables on errors (graceful degradation)

## Requirements

- Python 3.10+
- httpx >= 0.24.0
- pydantic >= 1.10.0

## Testing

Run the test suite:

```bash
# Install development dependencies
uv pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=railtown --cov-report=html

# Run specific test file
pytest tests/test_ingest_client.py
```

## License

MIT

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/railtownai/railengine-sdk).
