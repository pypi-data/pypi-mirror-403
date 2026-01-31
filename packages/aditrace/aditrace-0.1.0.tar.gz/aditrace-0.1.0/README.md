# Aditrace Python Client

A Python client for sending events to Aditrace.

## Installation

```bash
pip install aditrace
```

## Usage

```python
from aditrace.client import AdiTraceClient

client = AdiTraceClient(app_key="your_app_key", env="production")

try:
    # Your code that might raise an exception
    1 / 0
except Exception as e:
    client(e)
```
