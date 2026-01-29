"""Postman collection parsing library.

This is a generalized library for parsing Postman collections. Use programmatically:

```python
from postman import parse_postman_collection

# Parse a Postman collection
parsed = parse_postman_collection("collection.json")

# Access parsed requests
for request in parsed.requests:
    print(f"{request.method} {request.url}")
```
"""

from __future__ import annotations

# This is a library module - import and use the functions programmatically
