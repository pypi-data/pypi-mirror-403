# SIGNAL.ZERO Python SDK

Official Python SDK for SIGNAL.ZERO.

## Install

```bash
pip install signalzero-sdk
```

## Usage

### Public client (no API key)

```python
from signalzero_sdk import SignalZeroPublicClient

client = SignalZeroPublicClient(base_url="https://www.signalzero.ink")
status = client.wallet_status("0xYOUR_ADDRESS", chain_id=84532)
print(status)
```

### Partner client (server-side only)

```python
import os
from signalzero_sdk import SignalZeroPartnerClient

client = SignalZeroPartnerClient(
  base_url="https://www.signalzero.ink",
  api_key=os.environ["SIGNALZERO_API_KEY"],
)

history = client.wallet_history("0xYOUR_ADDRESS", limit=200)
print(history)
```

## Error handling

On API errors, the SDK raises `SignalZeroError` with `status_code` and `error` (the server error code).
