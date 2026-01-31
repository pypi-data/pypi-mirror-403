from __future__ import annotations

from typing import Self

from clearskies.columns import Boolean, Json, String

from clearskies_gitlab.rest import gitlab_member
from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestGroupMember(
    gitlab_member.GitlabMember,
):
    """
    Model for GitLab group members.

    This model provides access to the GitLab Group Members API for managing
    user membership in groups. It allows listing, adding, updating, and removing
    members from a group.

    See https://docs.gitlab.com/api/members/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupMember


    def my_function(group_members: GitlabRestGroupMember):
        # List all members of a group
        for member in group_members.where("group_id=123"):
            print(f"Member: {member.username}, Access Level: {member.access_level}")

        # Find a specific member
        admin = group_members.find("username=admin")
        if admin:
            print(f"Admin access level: {admin.access_level}")

        # Add a new member
        new_member = group_members.create(
            {
                "group_id": "123",
                "user_id": 456,
                "access_level": 30,  # Developer
            }
        )
    ```
    """

    id_column_name = "id"
    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/members"

    """
    The ID of the group to list members for.

    Used to scope API requests to a specific group.
    """
    group_id = String()

    """
    Search query to filter members by name or username.
    """
    query = String()

    """
    List of user IDs to filter results.
    """
    user_ids = Json()

    """
    List of user IDs to exclude from results.
    """
    skip_users = Json()

    """
    Whether to include seat usage information in the response.

    Only available for groups with a paid subscription.
    """
    show_seat_info = Boolean()

    """
    Whether to include inherited members from parent groups.

    When True, returns all members including those inherited from parent groups.
    """
    all = Boolean()
