# Apertis Python SDK Design

**Date:** 2026-01-23
**Status:** Approved
**Author:** Claude + User

## Overview

Python SDK for Apertis AI API, providing a standalone HTTP client for chat completions and embeddings. Designed to be framework-agnostic with an API style familiar to users of OpenAI/Anthropic SDKs.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package Name | `apertis` | Simple, available on PyPI, follows `openai`/`anthropic` convention |
| API Style | Async-first with sync wrapper | Streaming needs async; modern Python apps use async |
| HTTP Client | `httpx` | Native async/sync, SSE support, industry standard |
| Validation | `pydantic` v2 | Type safety, serialization, modern Python |
| Python Version | ≥3.9 | Balance of modern features and compatibility |
| Build Tool | Hatchling | Modern Python packaging standard |
| License | Apache-2.0 | Matches TypeScript SDK |

## Package Structure

```
apertis/
├── __init__.py          # Main exports: Apertis, AsyncApertis
├── _client.py           # Core client implementation
├── _base_client.py      # Shared HTTP logic
├── _streaming.py        # SSE streaming handler
├── _exceptions.py       # Custom exceptions
├── _constants.py        # Constants (API URL, version)
├── types/
│   ├── __init__.py
│   ├── chat.py          # Chat completion types
│   ├── embeddings.py    # Embedding types
│   └── shared.py        # Shared types (Usage, Error)
└── resources/
    ├── __init__.py
    ├── chat/
    │   ├── __init__.py
    │   └── completions.py  # chat.completions.create()
    └── embeddings.py       # embeddings.create()
```

## API Design

### Client Initialization

```python
from apertis import Apertis, AsyncApertis

# Sync client
client = Apertis(
    api_key="...",                          # or APERTIS_API_KEY env var
    base_url="https://api.apertis.ai/v1",   # customizable
    timeout=60.0,                           # default 60s
    max_retries=2,                          # auto-retry on 429, 5xx
    default_headers={"X-Custom": "..."},    # extra headers
)

# Async client
async_client = AsyncApertis(api_key="...")
```

### Chat Completions

```python
# Basic usage
response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=1000,
)

print(response.choices[0].message.content)
print(response.usage.total_tokens)

# Streaming (sync)
stream = client.chat.completions.create(
    model="gpt-5.2",
    messages=[...],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")

# Streaming (async)
async for chunk in await async_client.chat.completions.create(..., stream=True):
    print(chunk.choices[0].delta.content, end="")

# Tool calling
response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[...],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {"type": "object", "properties": {...}}
        }
    }],
    tool_choice="auto"
)

for tool_call in response.choices[0].message.tool_calls:
    print(tool_call.function.name, tool_call.function.arguments)
```

### Embeddings

```python
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Hello world",           # single string or list
    dimensions=1536,               # optional
)

embedding = response.data[0].embedding  # list[float]
```

### Error Handling

```python
from apertis import (
    ApertisError,          # Base exception
    APIError,              # API errors (4xx, 5xx)
    AuthenticationError,   # 401
    RateLimitError,        # 429
    APIConnectionError,    # Network issues
    APITimeoutError,       # Timeout
)

try:
    response = client.chat.completions.create(...)
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
except RateLimitError as e:
    print(f"Rate limited, retry after: {e.response.headers.get('retry-after')}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

**Exception Hierarchy:**

```
ApertisError (base)
├── APIError (has HTTP response)
│   ├── AuthenticationError (401)
│   ├── PermissionDeniedError (403)
│   ├── NotFoundError (404)
│   ├── RateLimitError (429)
│   └── InternalServerError (500+)
├── APIConnectionError (network issues)
└── APITimeoutError (timeout)
```

## Type Definitions

### Chat Types

```python
class ChatCompletionMessage(BaseModel):
    role: Literal["assistant"]
    content: str | None
    tool_calls: list[ToolCall] | None = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter"] | None

class ChatCompletion(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage | None = None
```

### Embedding Types

```python
class Embedding(BaseModel):
    object: Literal["embedding"]
    embedding: list[float]
    index: int

class EmbeddingResponse(BaseModel):
    object: Literal["list"]
    data: list[Embedding]
    model: str
    usage: EmbeddingUsage
```

## Dependencies

```toml
[project]
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "typing-extensions>=4.7.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "respx", "ruff", "mypy"]
```

## Testing Strategy

```
tests/
├── conftest.py           # pytest fixtures, mock client
├── test_client.py        # Client initialization
├── test_chat.py          # Chat completions
├── test_embeddings.py    # Embeddings
├── test_streaming.py     # Streaming
└── test_errors.py        # Error handling
```

- Use `respx` to mock HTTP requests (no real API calls)
- `pytest-asyncio` for async tests
- Cover: normal responses, streaming, error scenarios, retry logic

## Implementation Plan

1. **Phase 1: Core Infrastructure**
   - [ ] pyproject.toml setup
   - [ ] Base client with HTTP logic
   - [ ] Exception classes
   - [ ] Constants and configuration

2. **Phase 2: Types**
   - [ ] Shared types (Usage, Error)
   - [ ] Chat completion types
   - [ ] Embedding types
   - [ ] Streaming chunk types

3. **Phase 3: Resources**
   - [ ] Chat completions (non-streaming)
   - [ ] Chat completions (streaming)
   - [ ] Embeddings

4. **Phase 4: Polish**
   - [ ] Sync wrapper for async client
   - [ ] Retry logic
   - [ ] Tests
   - [ ] README and examples

## Estimated Scope

- **Files:** ~15 core files
- **Lines of Code:** ~800-1000
- **Based on:** TypeScript SDK (~700 lines)
