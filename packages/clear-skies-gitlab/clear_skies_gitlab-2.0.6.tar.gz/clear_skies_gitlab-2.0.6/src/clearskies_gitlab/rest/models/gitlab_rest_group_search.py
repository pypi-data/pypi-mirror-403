from __future__ import annotations

from typing import Self

from clearskies.columns import Integer

from clearskies_gitlab.rest.models import gitlab_rest_advanced_search


class GitlabRestGroupSearch(
    gitlab_rest_advanced_search.GitlabRestAdvancedSearch,
):
    """
    Model for GitLab group-scoped search.

    This model extends GitlabRestAdvancedSearch to provide search functionality
    scoped to a specific group. It allows searching for content within a group
    and its projects.

    See https://docs.gitlab.com/api/search/#group-search-api for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupSearch


    def my_function(group_search: GitlabRestGroupSearch):
        # Search for issues within a group
        for result in group_search.where("group_id=123").where("scope=issues").where("search=bug"):
            print(f"Found issue: {result.fields}")

        # Search for code within a group
        for result in group_search.where("group_id=123").where("scope=blobs").where("search=TODO"):
            print(f"Found code match: {result.fields}")
    ```
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/search"

    """
    The ID of the group to search within.

    Limits the search scope to this group and its projects.
    """
    group_id = Integer()
