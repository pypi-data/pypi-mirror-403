# Pokit Stack

Stack is an experimental ASGI Python framework for building JSON APIs. It is in early development and is not suitable
for production use. Any APIs exposed by this framework are subject to change without notice.

## Installation

```bash
pip install pokit-stack
```

## Example Program

`example.py`

```python
import json

from pokit.stack import Stack
from pokit.stack.types import HTTPMethod, RequestContext


async def home(request: RequestContext) -> str:
    assert request.method == HTTPMethod.GET

    out = f"Hello World! You are on path: {request.path}, using the method: {request.method}"

    out += "\n\n==== Query Params ====\n\n"
    out += json.dumps(request.query, indent=4)

    out += "\n\n==== Request Headers ====\n\n"
    out += json.dumps(request.headers, indent=4)

    return out


app = Stack(handler=home)
```

```bash
uvicorn example:app
```