---
title: Models
description: A guide on how to work with models using the WriftAI Python client
---

This section demonstrates common model operations you can perform with the WriftAI
Python client. These examples are not exhaustive — check the [client reference](../reference/) for all options.

## Get a model

```python
model = wriftai.models.get("deepseek-ai/deepseek-r1")
```

## Create a model

```python
model = wriftai.models.create({
    "name": "your-model",
    "hardware_identifier": "cpu",
})
```

## Delete a model

```python
wriftai.models.delete("your-username/your-model")
```

## Search models

```python
# returns models matching the query
models = wriftai.models.search("llama")
```

## List models

### All public models

```python
models = wriftai.models.list()
```

### Public models of a specific owner

```python
models = wriftai.models.list(owner="deepseek-ai")
```

### Public models sorted by their prediction count in descending order

```python
from wriftai.common_types import SortDirection
from wriftai.models import ModelsSortBy


models = wriftai.models.list(
    pagination_options={
        "sort_by": ModelsSortBy.PREDICTIONS_COUNT,
        "sort_direction": SortDirection.DESC,
    }
)
```

## Update a model

```python
updated_model = wriftai.models.update(
    "your-username/your-model",
    {"name": "your-new-model-name"},
)
```

## Get a version of a model

```python
model_version = wriftai.model_versions.get(
    "deepseek-ai/deepseek-r1:2",
)
```

## List versions of a model

```python
model_versions = wriftai.model_versions.list("deepseek-ai/deepseek-r1")
```
