"""Read-only integration tests for the Canny SDK.

IMPORTANT: These tests ONLY use read operations. They do NOT create,
modify, or delete any data in the Canny workspace.

To run these tests:
    CANNY_API_KEY=your_api_key pytest tests/integration/
"""

import pytest

from canny import CannyClient, CannyReadOnlyError


class TestBoardsReadOnly:
    """Test Boards API (read-only operations)."""

    def test_list_boards(self, live_client: CannyClient) -> None:
        """Test listing all boards."""
        response = live_client.boards.list()

        # Should have at least one board
        assert len(response.boards) >= 1

        # Verify board structure
        board = response.boards[0]
        assert board.id
        assert board.name
        assert board.url
        assert board.post_count >= 0

    def test_retrieve_board(self, live_client: CannyClient) -> None:
        """Test retrieving a specific board."""
        # First get a board ID from the list
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        board_id = boards.boards[0].id

        # Retrieve the specific board
        board = live_client.boards.retrieve(id=board_id)

        assert board.id == board_id
        assert board.name


class TestPostsReadOnly:
    """Test Posts API (read-only operations)."""

    def test_list_posts(self, live_client: CannyClient) -> None:
        """Test listing posts."""
        # Get a board first
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        board_id = boards.boards[0].id

        # List posts from the board
        response = live_client.posts.list(board_id=board_id, limit=5)

        # Should return a list (may be empty)
        assert hasattr(response, "posts")

        # If there are posts, verify structure
        if response.posts:
            post = response.posts[0]
            assert post.id
            assert post.title
            assert post.url

    def test_retrieve_post(self, live_client: CannyClient) -> None:
        """Test retrieving a specific post."""
        # Get a board and its posts
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        posts = live_client.posts.list(board_id=boards.boards[0].id, limit=1)
        if not posts.posts:
            pytest.skip("No posts available")

        post_id = posts.posts[0].id

        # Retrieve the specific post
        post = live_client.posts.retrieve(id=post_id)

        assert post.id == post_id
        assert post.title


class TestUsersReadOnly:
    """Test Users API (read-only operations)."""

    def test_list_users(self, live_client: CannyClient) -> None:
        """Test listing users with v2 pagination."""
        response = live_client.users.list(limit=5)

        # Should return a list
        assert hasattr(response, "users")
        assert hasattr(response, "has_next_page")

        # If there are users, verify structure
        if response.users:
            user = response.users[0]
            assert user.id
            assert user.name


class TestCategoriesReadOnly:
    """Test Categories API (read-only operations)."""

    def test_list_categories(self, live_client: CannyClient) -> None:
        """Test listing categories for a board."""
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        response = live_client.categories.list(board_id=boards.boards[0].id)

        # Should return a list (may be empty)
        assert hasattr(response, "categories")


class TestTagsReadOnly:
    """Test Tags API (read-only operations)."""

    def test_list_tags(self, live_client: CannyClient) -> None:
        """Test listing tags for a board."""
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        response = live_client.tags.list(board_id=boards.boards[0].id)

        # Should return a list (may be empty)
        assert hasattr(response, "tags")


class TestVotesReadOnly:
    """Test Votes API (read-only operations)."""

    def test_list_votes(self, live_client: CannyClient) -> None:
        """Test listing votes."""
        # Get a post first
        boards = live_client.boards.list()
        if not boards.boards:
            pytest.skip("No boards available")

        posts = live_client.posts.list(board_id=boards.boards[0].id, limit=1)
        if not posts.posts:
            pytest.skip("No posts available")

        response = live_client.votes.list(post_id=posts.posts[0].id, limit=5)

        # Should return a list (may be empty)
        assert hasattr(response, "votes")


class TestReadOnlyModeEnforcement:
    """Test that read-only mode blocks write operations."""

    def test_create_post_blocked(self, live_client: CannyClient) -> None:
        """Verify that creating a post is blocked in read-only mode."""
        with pytest.raises(CannyReadOnlyError) as exc_info:
            live_client.posts.create(
                author_id="fake_author",
                board_id="fake_board",
                title="Test Post",
                details="This should not be created",
            )

        assert "read-only mode" in str(exc_info.value)

    def test_delete_post_blocked(self, live_client: CannyClient) -> None:
        """Verify that deleting a post is blocked in read-only mode."""
        with pytest.raises(CannyReadOnlyError) as exc_info:
            live_client.posts.delete(post_id="fake_post_id")

        assert "read-only mode" in str(exc_info.value)

    def test_create_vote_blocked(self, live_client: CannyClient) -> None:
        """Verify that creating a vote is blocked in read-only mode."""
        with pytest.raises(CannyReadOnlyError) as exc_info:
            live_client.votes.create(
                post_id="fake_post",
                voter_id="fake_voter",
            )

        assert "read-only mode" in str(exc_info.value)

    def test_client_is_read_only(self, live_client: CannyClient) -> None:
        """Verify the client reports read-only status."""
        assert live_client.is_read_only is True
