---
title: Initializing
description: Guide on how to initialize the WriftAI Python client
---

This section demonstrates how to initialize the WriftAI Python client with practical examples.

## Basic Initialization

If your environment variables are set (`WRIFTAI_ACCESS_TOKEN` and optionally `WRIFTAI_API_BASE_URL`),
you can initialize the client without passing any options.

```python
from wriftai import Client


wriftai = Client()
```

This automatically uses:

- `WRIFTAI_ACCESS_TOKEN` environment variable if present; otherwise requests are **unauthenticated**
- `WRIFTAI_API_BASE_URL` environment variable if present; otherwise the **default API base URL** is used
- Default configuration for the sync and async `httpx` clients along with a request timeout of 10 seconds.

## Custom Initialization

If you want full control or are not using environment variables, you can provide options manually.

### Use a Specific API Base URL

```python
from wriftai import Client


wriftai = Client(api_base_url="https://api.wrift.ai/v1")
```

### Provide an Access Token Directly

```python
from wriftai import Client


wriftai = Client(access_token="your_access_token_here")
```

### Provide custom `httpx` configuration

```python
import httpx
from wriftai import Client


wriftai = Client(
    client_options={
        "headers": {
            "X-App-Name": "my-app",
        },
        "timeout": httpx.Timeout(10.0),
        "transport": httpx.HTTPTransport(),
    }
)
```
