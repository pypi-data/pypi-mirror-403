# SMM (SOCIAL MEDIA MARKETING)

A lightweight, zero-dependency Python client for connecting to compatible SMM (Social Media Marketing) Panels.

## Features
- **Zero Dependencies**: Built with native libraries (actually uses `requests` which is standard).
- **Python Support**: Full type hinting included.
- **Universal**: Works in Python 3.6+.

## Installation

```bash
pip install smmpy
```

## Usage

```python
from smmpy import smm

# Initialize
client = smm('https://smm-provider.com/api/v2', 'YOUR_API_KEY')

# Get Balance
balance = client.get_balance()
print(balance)

# Add Order
order = client.add_order(
    service=123,
    link='https://example.com',
    quantity=1000
)

# Get Status
status = client.get_status(order['order'])
```

## API Reference
- `get_services()`
- `add_order(service, link, quantity, comments=None, runs=None, interval=None)`
- `get_status(order_id)`
- `get_multi_status(order_ids)`
- `create_refill(order_id)`
- `get_refill_status(refill_id)`
- `cancel_orders(order_ids)`
- `get_balance()`

## License
MIT
