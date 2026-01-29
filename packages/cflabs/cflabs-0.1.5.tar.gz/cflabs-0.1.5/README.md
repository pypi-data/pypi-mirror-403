# CFLabs SDK

Python SDK for interacting with the CFLabs/Octavian API.

## Installation

```bash
pip install cflabs
```

## Usage

```python
from cflabs import CFLabs

# Initialize the client
client = CFLabs(
    api_key="your-api-key",  # or set CFLABS_API_KEY environment variable
    base_url="https://api.cflabs.com"  # optional, defaults to localhost:8000
)

# Run a prompt by ID
result = client.run(
    var_parameters={"input": "your input"}
)

# Or use a prompt slug
from cflabs import Prompt

prompt = Prompt(slug="my-prompt-slug", client=client)
result = prompt.run(var_parameters={"input": "your input"})
```

## Configuration

The SDK can be configured using:
- Constructor arguments
- Environment variables: `CFLABS_API_KEY`

## Requirements

- Python >= 3.8
- requests >= 2.31.0

## License

MIT
