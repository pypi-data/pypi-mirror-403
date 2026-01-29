# sdata

A simple Python client for calling the sdata FastAPI service.

## Installation

```bash
pip install .
```

## Usage

```python
from sdata import SDataClient

client = SDataClient("http://localhost:8000")
result = client.call_api("get_ticks", {"security": "000001.XSHE", "count": 8})
print(result)
```
