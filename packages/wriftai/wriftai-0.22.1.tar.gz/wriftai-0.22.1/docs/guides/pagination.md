---
title: Pagination
description: A guide on how to paginate through items using the WriftAI Python client
---

Operations that return lists of resources from WriftAI's API use **cursor‑based pagination**, allowing you to
fetch data in manageable chunks instead of retrieving everything at once.

This guide explains how to fetch the first page, request additional pages, and handle pagination cursors.

## Fetch the first page

If you don't pass any options, the first page is returned.

```python
page = wriftai.models.list()
```

## Fetch the first page with a custom page size

You can control the maximum number of items returned in each page.

```python
page = wriftai.models.list({"page_size": 15})
```

## Fetch the next page

Use the next cursor returned in the page response.

```python
if page.next_cursor:
    next_page = wriftai.models.list({"cursor": page.next_cursor})
```

If `next_cursor` is `None`, you are on the last page.

## Fetch the previous page

Use the previous page cursor from the page response.

```python
if page.previous_cursor:
    previous_page = wriftai.models.list({"cursor": page.previous_cursor})
```

If `previous_cursor` is `None`, you are on the first page.

## Iterate through all pages

You can loop through pages by repeatedly requesting the next page until no next cursor is returned.

```python
page = wriftai.models.list()

while page.next_cursor:
    page = wriftai.models.list({"cursor": page.next_cursor})

    # process page.items
```

## Iterate backwards through pages

If you start from a page other than the first, you can page backwards using the previous cursor.

```python
while page.previous_cursor:
    page = wriftai.models.list({"cursor": page.previous_cursor})

    # process page.items
```
