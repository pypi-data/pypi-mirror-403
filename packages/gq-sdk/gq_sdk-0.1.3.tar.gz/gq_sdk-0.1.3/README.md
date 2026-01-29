# gq-sdk

Python SDK for the GoQuant Trading Platform.

## Installation

```bash
pip install gq-sdk
```

## Quick Start

```python
from gq_sdk import Client

client = Client("https://your-backend-url.com", "your-api-key")
client.authenticate("email", "password")
client.login_exchange("okx", "account", "key", "secret", "pass")
algo_id = client.place_market_edge_order("okx", "account", "BTC-USDT-SWAP", "buy", 0.01, 60)
print(f"Order: {algo_id}")
```

## Documentation

For full API documentation: https://docs.goquant.io

## Support

Email: support@goquant.io

## License

Proprietary License - See LICENSE file for details.
