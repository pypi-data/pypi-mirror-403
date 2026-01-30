"""Synchronous Canny client."""

from typing import Any, Optional

from .config import CannyConfig
from .http import CannyHTTPClient
from .resources.boards import BoardsResource
from .resources.categories import CategoriesResource
from .resources.comments import CommentsResource
from .resources.companies import CompaniesResource
from .resources.entries import EntriesResource
from .resources.groups import GroupsResource
from .resources.posts import PostsResource
from .resources.status_changes import StatusChangesResource
from .resources.tags import TagsResource
from .resources.users import UsersResource
from .resources.votes import VotesResource


class CannyClient:
    """Synchronous client for the Canny API.

    Example:
        ```python
        from canny import CannyClient

        # Initialize with API key from environment variable CANNY_API_KEY
        client = CannyClient()

        # Or with explicit API key
        client = CannyClient(api_key="your_api_key")

        # Safe mode (default) - blocks write operations
        client = CannyClient(read_only=True)

        # Allow write operations
        client = CannyClient(read_only=False)

        # List all boards
        boards = client.boards.list()
        for board in boards.boards:
            print(board.name)

        # List posts with automatic pagination
        for post in client.posts.list_all(board_id="..."):
            print(post.title)
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
        """Initialize the Canny client.

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
        self._http = CannyHTTPClient(self._config)

        # Initialize resource accessors
        self._boards = BoardsResource(self._http, self._config)
        self._categories = CategoriesResource(self._http, self._config)
        self._comments = CommentsResource(self._http, self._config)
        self._companies = CompaniesResource(self._http, self._config)
        self._entries = EntriesResource(self._http, self._config)
        self._groups = GroupsResource(self._http, self._config)
        self._posts = PostsResource(self._http, self._config)
        self._status_changes = StatusChangesResource(self._http, self._config)
        self._tags = TagsResource(self._http, self._config)
        self._users = UsersResource(self._http, self._config)
        self._votes = VotesResource(self._http, self._config)

    @property
    def boards(self) -> BoardsResource:
        """Access the Boards API."""
        return self._boards

    @property
    def categories(self) -> CategoriesResource:
        """Access the Categories API."""
        return self._categories

    @property
    def comments(self) -> CommentsResource:
        """Access the Comments API."""
        return self._comments

    @property
    def companies(self) -> CompaniesResource:
        """Access the Companies API."""
        return self._companies

    @property
    def entries(self) -> EntriesResource:
        """Access the Changelog Entries API."""
        return self._entries

    @property
    def groups(self) -> GroupsResource:
        """Access the Groups API."""
        return self._groups

    @property
    def posts(self) -> PostsResource:
        """Access the Posts API."""
        return self._posts

    @property
    def status_changes(self) -> StatusChangesResource:
        """Access the Status Changes API."""
        return self._status_changes

    @property
    def tags(self) -> TagsResource:
        """Access the Tags API."""
        return self._tags

    @property
    def users(self) -> UsersResource:
        """Access the Users API."""
        return self._users

    @property
    def votes(self) -> VotesResource:
        """Access the Votes API."""
        return self._votes

    @property
    def is_read_only(self) -> bool:
        """Check if the client is in read-only mode."""
        return self._config.read_only

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._http.close()

    def __enter__(self) -> "CannyClient":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()
