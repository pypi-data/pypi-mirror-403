from __future__ import annotations

from typing import Self

from clearskies.columns import Boolean, Json, String

from clearskies_gitlab.rest import gitlab_member
from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestProjectMember(
    gitlab_member.GitlabMember,
):
    """
    Model for GitLab project members.

    This model provides access to the GitLab Project Members API for managing
    project membership. It extends the base GitlabMember class with project-specific
    functionality.

    See https://docs.gitlab.com/api/members/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectMember


    def my_function(members: GitlabRestProjectMember):
        # List all members of a project
        for member in members.where("project_id=123"):
            print(f"Member: {member.username}")
            print(f"Access level: {member.access_level}")

        # Search for specific members
        for member in members.where("project_id=123&query=john"):
            print(f"Found: {member.name}")

        # Add a new member
        members.create(
            {
                "project_id": 123,
                "user_id": 456,
                "access_level": 30,  # Developer
            }
        )
    ```
    """

    backend = GitlabRestBackend()
    id_column_name = "id"

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/members"

    """
    The ID of the project to query members for.
    """
    project_id = String()

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
    Whether to include seat information in the response.

    Only available for groups with a paid plan.
    """
    show_seat_info = Boolean()

    """
    Whether to include inherited members.

    When true, includes members inherited from parent groups.
    """
    all = Boolean()
