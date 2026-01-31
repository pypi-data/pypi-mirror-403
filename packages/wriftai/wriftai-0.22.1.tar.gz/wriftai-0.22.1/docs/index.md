---
title: Introduction
description: Overview of the WriftAI Python library and installation guide
---

The WriftAI Python Client provides convenient access to WriftAI's services. The library includes type definitions
for all request params and response fields, and offers both synchronous and asynchronous clients powered
by [httpx](https://github.com/encode/httpx).

## Source Code

The WriftAI Python client is open‑source. You can explore the codebase, track changes, or report issues using the links below:

- **Repository**: https://github.com/wriftai/wriftai-python
- **Issues**: https://github.com/wriftai/wriftai-python/issues
- **Releases**: https://github.com/wriftai/wriftai-python/releases

## Requirements
- Python 3.10+

## Installation
```bash
pip install wriftai
```

## Using AsyncIO

The WriftAI Python client includes asyncio support powered by `httpx`. For convenience, every method also has an `async_` prefixed variant.
