"""Asynchronous Canny client."""

from typing import Any, Optional

from .config import CannyConfig
from .http import CannyAsyncHTTPClient
from .resources.boards import BoardsAsyncResource
from .resources.categories import CategoriesAsyncResource
from .resources.comments import CommentsAsyncResource
from .resources.companies import CompaniesAsyncResource
from .resources.entries import EntriesAsyncResource
from .resources.groups import GroupsAsyncResource
from .resources.posts import PostsAsyncResource
from .resources.status_changes import StatusChangesAsyncResource
from .resources.tags import TagsAsyncResource
from .resources.users import UsersAsyncResource
from .resources.votes import VotesAsyncResource


class CannyAsyncClient:
    """Asynchronous client for the Canny API.

    Example:
        ```python
        import asyncio
        from canny import CannyAsyncClient

        async def main():
            async with CannyAsyncClient() as client:
                # List all boards
                boards = await client.boards.list()
                for board in boards.boards:
                    print(board.name)

                # Fetch data concurrently
                import asyncio
                boards, users = await asyncio.gather(
                    client.boards.list(),
                    client.users.list()
                )

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        read_only: bool = True,
        timeout: float = 30.0,
        base_url_v1: str = "https://canny.io/api/v1/",
        base_url_v2: str = "https://canny.io/api/v2/",
    ):
        """Initialize the async Canny client.

        Args:
            api_key: Your Canny API key. If not provided, reads from
                     CANNY_API_KEY environment variable.
            read_only: If True (default), blocks all write operations.
                       Set to False to allow create, update, delete operations.
            timeout: Request timeout in seconds.
            base_url_v1: Base URL for v1 API endpoints.
            base_url_v2: Base URL for v2 API endpoints.
        """
        self._config = CannyConfig(
            api_key=api_key,
            read_only=read_only,
            timeout=timeout,
            base_url_v1=base_url_v1,
            base_url_v2=base_url_v2,
        )
        self._http = CannyAsyncHTTPClient(self._config)

        # Initialize resource accessors
        self._boards = BoardsAsyncResource(self._http, self._config)
        self._categories = CategoriesAsyncResource(self._http, self._config)
        self._comments = CommentsAsyncResource(self._http, self._config)
        self._companies = CompaniesAsyncResource(self._http, self._config)
        self._entries = EntriesAsyncResource(self._http, self._config)
        self._groups = GroupsAsyncResource(self._http, self._config)
        self._posts = PostsAsyncResource(self._http, self._config)
        self._status_changes = StatusChangesAsyncResource(self._http, self._config)
        self._tags = TagsAsyncResource(self._http, self._config)
        self._users = UsersAsyncResource(self._http, self._config)
        self._votes = VotesAsyncResource(self._http, self._config)

    @property
    def boards(self) -> BoardsAsyncResource:
        """Access the Boards API."""
        return self._boards

    @property
    def categories(self) -> CategoriesAsyncResource:
        """Access the Categories API."""
        return self._categories

    @property
    def comments(self) -> CommentsAsyncResource:
        """Access the Comments API."""
        return self._comments

    @property
    def companies(self) -> CompaniesAsyncResource:
        """Access the Companies API."""
        return self._companies

    @property
    def entries(self) -> EntriesAsyncResource:
        """Access the Changelog Entries API."""
        return self._entries

    @property
    def groups(self) -> GroupsAsyncResource:
        """Access the Groups API."""
        return self._groups

    @property
    def posts(self) -> PostsAsyncResource:
        """Access the Posts API."""
        return self._posts

    @property
    def status_changes(self) -> StatusChangesAsyncResource:
        """Access the Status Changes API."""
        return self._status_changes

    @property
    def tags(self) -> TagsAsyncResource:
        """Access the Tags API."""
        return self._tags

    @property
    def users(self) -> UsersAsyncResource:
        """Access the Users API."""
        return self._users

    @property
    def votes(self) -> VotesAsyncResource:
        """Access the Votes API."""
        return self._votes

    @property
    def is_read_only(self) -> bool:
        """Check if the client is in read-only mode."""
        return self._config.read_only

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> "CannyAsyncClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()
