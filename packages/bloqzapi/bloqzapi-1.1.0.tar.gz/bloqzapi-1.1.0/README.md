# Bloqz Python SDK

Official Python SDK for the Bloqz Intent API. Convert financial intent from natural language into deterministic execution plans.

## Installation

```bash
pip install bloqzapi
```

## Quick Start

```python
from bloqzapi import BloqzClient
import os

client = BloqzClient(
    base_url="http://localhost:4000",
    api_key=os.environ["BLOQZ_API_KEY"]
)

# Parse intent from natural language
intent = client.parse_intent({
    "text": "Swap 100 USDC to ETH",
    "context": { "session_id": "demo-1" }
})

# Build execution plan
plan = client.build_plan({
    "text": "Stake $40 of ETH on Ethereum",
    "context": { "session_id": "demo-1", "proof_signer": "user-123" }
})

# Simulate plan
simulation = client.simulate_plan({
    "text": "Swap 100 USDC to ETH"
})

# Validate plan
validation = client.validate_plan(plan_object)

# Verify plan proof
verification = client.verify_plan(plan_object)
```

## Configuration

- `base_url` - API base URL (default: `http://localhost:4000`)
- `api_key` - Your API key (required for product endpoints)
- `timeout` - Request timeout in seconds (default: 30)
- `max_retries` - Maximum retry attempts (default: 2)

## Documentation

Full documentation available at: https://bloqz.io/docs

## License

UNLICENSED

