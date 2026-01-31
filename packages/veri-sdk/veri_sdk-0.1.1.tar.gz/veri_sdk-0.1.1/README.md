# veri-sdk

Official Python SDK for the Veri AI Deepfake Detection API.

## Installation

```bash
pip install veri-sdk
```

## Quick Start

```python
from veri import VeriClient

# Create a client with your API key
client = VeriClient(api_key="your-api-key-here")

# Detect an image
with open("image.jpg", "rb") as f:
    result = client.detect(f)

print(f"Prediction: {result.prediction}")
print(f"Is AI-generated: {result.is_fake}")
print(f"Confidence: {result.confidence:.1%}")
```

## Usage Examples

### Detect from File Path

```python
from pathlib import Path
from veri import VeriClient

client = VeriClient(api_key="your-api-key")

result = client.detect(Path("suspicious-image.jpg"))

if result.is_fake:
    print("This image appears to be AI-generated")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Verdict: {result.verdict}")
else:
    print("This image appears to be authentic")
```

### Detect from Bytes

```python
import requests
from veri import VeriClient

client = VeriClient(api_key="your-api-key")

# Download image and detect
response = requests.get("https://example.com/image.jpg")
result = client.detect(response.content)
```

### Detect from URL

```python
result = client.detect_url("https://example.com/image.jpg")
```

### With Detection Options

```python
from veri import VeriClient, DetectionOptions

client = VeriClient(api_key="your-api-key")

options = DetectionOptions(
    threshold=0.6,
)

result = client.detect(image_bytes, options=options)
```

### Get Profile

```python
profile = client.get_profile()
print(f"User ID: {profile['userId']}")
print(f"Credits: {profile['credits']}")
```

### Async Client

```python
import asyncio
from veri import AsyncVeriClient

async def main():
    async with AsyncVeriClient(api_key="your-api-key") as client:
        # Run multiple detections concurrently
        tasks = [
            client.detect(image1_bytes),
            client.detect(image2_bytes),
            client.detect(image3_bytes),
        ]
        results = await asyncio.gather(*tasks)

        for i, result in enumerate(results):
            print(f"Image {i+1}: {'FAKE' if result.is_fake else 'REAL'}")

asyncio.run(main())
```

## Error Handling

```python
from veri import (
    VeriClient,
    VeriAPIError,
    VeriValidationError,
    VeriRateLimitError,
    VeriTimeoutError,
)

client = VeriClient(api_key="your-api-key")

try:
    result = client.detect(image_bytes)
except VeriRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except VeriTimeoutError as e:
    print(f"Request timed out after {e.timeout_ms}ms")
except VeriAPIError as e:
    print(f"API Error: {e.message} (code: {e.code})")
    print(f"Request ID: {e.request_id}")
except VeriValidationError as e:
    print(f"Validation Error: {e.message} (field: {e.field})")
```

## Configuration

```python
client = VeriClient(
    api_key="your-api-key",
    base_url="https://api.veri.studio/v1",  # Custom API URL
    timeout=30.0,                         # Request timeout (seconds)
    max_retries=3,                        # Retry attempts
)
```

## Context Manager

Both sync and async clients support context managers:

```python
# Sync
with VeriClient(api_key="your-api-key") as client:
    result = client.detect(image_bytes)

# Async
async with AsyncVeriClient(api_key="your-api-key") as client:
    result = await client.detect(image_bytes)
```

## Model

| Model | Description |
|-------|-------------|
| `veri_face` | DenseNet-121 + MoE face forgery detector |

## Type Hints

This SDK is fully typed. Import types for your IDE:

```python
from veri import (
    DetectionResult,
    DetectionOptions,
    ModelResult,
)
```

## Requirements

- Python 3.10+
- httpx
- pydantic

## License

MIT
