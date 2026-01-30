"""API resource classes for the Canny SDK."""

from .boards import BoardsResource
from .categories import CategoriesResource
from .comments import CommentsResource
from .companies import CompaniesResource
from .entries import EntriesResource
from .groups import GroupsResource
from .posts import PostsResource
from .status_changes import StatusChangesResource
from .tags import TagsResource
from .users import UsersResource
from .votes import VotesResource

__all__ = [
    "BoardsResource",
    "CategoriesResource",
    "CommentsResource",
    "CompaniesResource",
    "EntriesResource",
    "GroupsResource",
    "PostsResource",
    "StatusChangesResource",
    "TagsResource",
    "UsersResource",
    "VotesResource",
]
