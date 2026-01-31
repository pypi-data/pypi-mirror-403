# sagellm-protocol

## Protocol Compliance (Mandatory)

- This repository defines Protocol v0.1 as the source of truth.
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added here before use.

[![CI](https://github.com/intellistream/sagellm-protocol/workflows/CI/badge.svg)](https://github.com/intellistream/sagellm-protocol/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-e92063.svg)](https://docs.pydantic.dev/2.0/)
[![Code Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](docs/TESTING.md)

Type definitions and validation for sageLLM inference engine.

- **Package**: `isagellm-protocol`
- **Import**: `sagellm_protocol`
- **Python**: 3.10+

## Installation

```bash
pip install isagellm-protocol
```

For development:

```bash
git clone git@github.com:intellistream/sagellm-protocol.git
cd sagellm-protocol
pip install -e ".[dev]"
```

## Features

- Request/Response type definitions
- Streaming event types (start/delta/end)
- Performance metrics with validation
- Error types and error codes
- Timestamp tracking
- KV cache lifecycle hooks
- Pydantic v2 validation

## Quick Start

```python
from sagellm_protocol import Request, Response, Metrics, ErrorCode

# 创建请求
req = Request(
    request_id="req-001",
    trace_id="trace-001",
    model="llama2-7b",
    prompt="Hello, world!",
    max_tokens=128,
    stream=False,
    temperature=0.7,
)

# 创建响应
metrics = Metrics(
    ttft_ms=45.2,
    tbt_ms=12.5,
    throughput_tps=80.0,
    peak_mem_mb=24576,
    error_rate=0.0,
)

resp = Response(
    request_id="req-001",
    trace_id="trace-001",
    output_text="Hi there!",
    output_tokens=[42, 17],
    finish_reason="stop",
    metrics=metrics,
)
```

For more examples, see [examples/basic_usage.py](examples/basic_usage.py).

## API Reference

### Core Types
- `Request` / `Response` - Request and response objects
- `Metrics` - Performance metrics
- `StreamEvent` - Streaming event types
- `Error` / `ErrorCode` - Error handling
- `Timestamps` - Timestamp tracking
- `KVAllocateParams` / `KVHandle` - KV cache management

## Development

Run tests:
```bash
pytest tests/ -v
```

Format and lint:
```bash
ruff format .
ruff check . --fix
```

Type check:
```bash
mypy src/sagellm_protocol
```

## Documentation

For more details:
- [Testing Guide](docs/TESTING.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## License

Proprietary - IntelliStream
