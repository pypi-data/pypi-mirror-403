# Simplex Python SDK

Official Python SDK for the [Simplex API](https://simplex.sh) - A powerful workflow automation platform for browser-based tasks.

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install simplex
```

## Quick Start

```python
import time
from simplex import SimplexClient

# Initialize the client
client = SimplexClient(api_key="your-api-key")

# Run a workflow
response = client.run_workflow(
    "workflow-id",
    variables={"email": "user@example.com"}
)

print(f"Session started: {response['session_id']}")

# Poll for completion
while True:
    status = client.get_session_status(response["session_id"])
    if not status["in_progress"]:
        break
    time.sleep(1)

# Check results
if status["success"]:
    print("Success!")
    print("Scraper outputs:", status["scraper_outputs"])
    print("File metadata:", status["file_metadata"])
else:
    print("Failed")
```

## API Reference

### SimplexClient

```python
client = SimplexClient(
    api_key="your-api-key",
    base_url="https://api.simplex.sh",  # Optional
    timeout=30,                          # Request timeout in seconds
    max_retries=3,                       # Retry attempts for failed requests
    retry_delay=1.0,                     # Delay between retries in seconds
)
```

### Methods

#### `run_workflow(workflow_id, variables=None, metadata=None, webhook_url=None)`

Run a workflow by its ID.

```python
response = client.run_workflow(
    "workflow-id",
    variables={"key": "value"},
    metadata="optional metadata",
    webhook_url="https://your-webhook.com/callback"
)

print(response["session_id"])  # Session ID for polling
print(response["vnc_url"])     # VNC URL to watch the session
```

#### `get_session_status(session_id)`

Get the status of a running or completed session.

```python
status = client.get_session_status("session-id")

print(status["in_progress"])       # True while running
print(status["success"])           # True/False when complete, None while running
print(status["scraper_outputs"])   # Data collected by scrapers
print(status["file_metadata"])     # Metadata for downloaded files
print(status["metadata"])          # Custom metadata
print(status["workflow_metadata"]) # Workflow metadata
```

#### `download_session_files(session_id, filename=None)`

Download files from a completed session.

```python
# Download all files as a zip
zip_data = client.download_session_files("session-id")
with open("files.zip", "wb") as f:
    f.write(zip_data)

# Download a specific file
pdf_data = client.download_session_files("session-id", filename="report.pdf")
with open("report.pdf", "wb") as f:
    f.write(pdf_data)
```

#### `retrieve_session_replay(session_id)`

Download the session replay video (MP4).

```python
video = client.retrieve_session_replay("session-id")
with open("replay.mp4", "wb") as f:
    f.write(video)
```

#### `retrieve_session_logs(session_id)`

Get the session logs as parsed JSON.

```python
logs = client.retrieve_session_logs("session-id")
for entry in logs:
    print(f"{entry['timestamp']}: {entry['message']}")
```

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from simplex import (
    SimplexClient,
    SimplexError,
    WorkflowError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    ValidationError,
)

client = SimplexClient(api_key="your-api-key")

try:
    result = client.run_workflow("workflow-id")
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except WorkflowError as e:
    print(f"Workflow error: {e.message}")
    print(f"Session ID: {e.session_id}")
except NetworkError as e:
    print(f"Network error: {e.message}")
except SimplexError as e:
    print(f"General error: {e.message}")
```

## Type Hints

The SDK includes full type hints for better IDE support:

```python
from simplex import (
    SimplexClient,
    SessionStatusResponse,
    RunWorkflowResponse,
    FileMetadata,
)

client = SimplexClient(api_key="your-api-key")
response: RunWorkflowResponse = client.run_workflow("workflow-id")
status: SessionStatusResponse = client.get_session_status(response["session_id"])
```

## Requirements

- Python 3.9+
- `requests>=2.25.0`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [https://docs.simplex.sh](https://docs.simplex.sh)
- Email: support@simplex.sh
