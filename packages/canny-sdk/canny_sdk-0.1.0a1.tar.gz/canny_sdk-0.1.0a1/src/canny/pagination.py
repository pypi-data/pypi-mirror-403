"""Pagination helpers for the Canny SDK."""

from collections.abc import Iterator
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class SkipPaginator(Generic[T]):
    """Paginator for skip-based pagination (v1 endpoints).

    Automatically fetches all pages of results by incrementing the skip parameter.

    Example:
        for post in SkipPaginator(
            fetch_fn=client.posts.list,
            items_key="posts",
            board_id="..."
        ):
            print(post.title)
    """

    def __init__(
        self,
        fetch_fn: Callable[..., Any],
        items_key: str,
        limit: int = 100,
        **kwargs: Any,
    ):
        """Initialize the paginator.

        Args:
            fetch_fn: The function to call to fetch a page of results.
            items_key: The key in the response that contains the list of items.
            limit: The number of items to fetch per page.
            **kwargs: Additional arguments to pass to the fetch function.
        """
        self._fetch_fn = fetch_fn
        self._items_key = items_key
        self._limit = limit
        self._kwargs = kwargs

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across all pages."""
        skip = 0
        while True:
            response = self._fetch_fn(limit=self._limit, skip=skip, **self._kwargs)
            items = getattr(response, self._items_key, [])

            yield from items

            # Check if there are more items
            has_more = getattr(response, "has_more", False)
            if not has_more or len(items) < self._limit:
                break

            skip += len(items)


class CursorPaginator(Generic[T]):
    """Paginator for cursor-based pagination (v2 endpoints).

    Automatically fetches all pages of results using cursor tokens.

    Example:
        for user in CursorPaginator(
            fetch_fn=client.users.list,
            items_key="users"
        ):
            print(user.name)
    """

    def __init__(
        self,
        fetch_fn: Callable[..., Any],
        items_key: str,
        limit: int = 100,
        **kwargs: Any,
    ):
        """Initialize the paginator.

        Args:
            fetch_fn: The function to call to fetch a page of results.
            items_key: The key in the response that contains the list of items.
            limit: The number of items to fetch per page.
            **kwargs: Additional arguments to pass to the fetch function.
        """
        self._fetch_fn = fetch_fn
        self._items_key = items_key
        self._limit = limit
        self._kwargs = kwargs

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across all pages."""
        cursor: Optional[str] = None

        while True:
            if cursor:
                response = self._fetch_fn(limit=self._limit, cursor=cursor, **self._kwargs)
            else:
                response = self._fetch_fn(limit=self._limit, **self._kwargs)

            items = getattr(response, self._items_key, [])

            yield from items

            # Check if there are more pages
            has_next = getattr(response, "has_next_page", False)
            cursor = getattr(response, "cursor", None)

            if not has_next or not cursor:
                break
