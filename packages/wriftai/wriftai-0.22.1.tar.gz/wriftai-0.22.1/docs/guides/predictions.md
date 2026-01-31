---
title: Predictions
description: A guide on how to work with predictions using the WriftAI Python client
---

This section demonstrates common prediction operations you can perform with the WriftAI
Python client. These examples are not exhaustive — check the [client reference](../reference/) for all options.

## Get a Prediction by ID

```python
prediction = wriftai.predictions.get("your-prediction-id")
```

## Create a Prediction

### With the latest version of a model

```python
prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        }
    },
)
```

### With a specific version of a model

```ts
prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1:2",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        }
    },
)
```

### With a webhook for prediction updates

```python
prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        },
        "webhook": {
            "url": "https://example.com/webhooks/wriftai",
            "secret": "top-secret",  # This is optional
        },
    },
)
```

### With input validation enabled

Enable early input validation against the model’s input schema before a prediction is created.
This catches invalid inputs upfront and prevents unnecessary model execution and cost.

```python
prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        },
        "validate_input": True
    },
)
```

### Create and wait for completion

```python
prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        }
    },
    wait=True
)
```

### Create and wait with custom options

```python
from wriftai.predictions import PredictionWithIO, WaitOptions


def on_poll(prediction: PredictionWithIO) -> None:
    # your custom logic
    return


prediction = wriftai.predictions.create(
    model="deepseek-ai/deepseek-r1",
    params={
        "input": {
            "prompt": "Summarize quantum computing.",
        }
    },
    wait=True,
    wait_options=WaitOptions(poll_interval=500, on_poll=on_poll),
)
```

## Wait for an existing prediction to complete

```python
prediction = wriftai.predictions.wait("your-prediction-id")
```

## List Predictions

```python
predictions = wriftai.predictions.list()
```