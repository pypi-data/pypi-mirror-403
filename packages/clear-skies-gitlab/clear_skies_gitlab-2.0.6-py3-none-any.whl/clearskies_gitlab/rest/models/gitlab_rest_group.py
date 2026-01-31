from __future__ import annotations

from typing import Self

from clearskies.columns import (
    HasMany,
)

from clearskies_gitlab.rest.models import (
    gitlab_rest_group_access_token_reference,
    gitlab_rest_group_base,
    gitlab_rest_group_member_reference,
    gitlab_rest_group_project_reference,
    gitlab_rest_group_subgroup_reference,
    gitlab_rest_group_variable_reference,
)


class GitlabRestGroup(
    gitlab_rest_group_base.GitlabRestGroupBase,
):
    """
    Model for GitLab groups.

    This model provides access to the GitLab Groups API for managing groups and their
    associated resources. Groups are used to organize projects and manage permissions
    for teams of users.

    See https://docs.gitlab.com/api/groups/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroup


    def my_function(groups: GitlabRestGroup):
        # List all groups
        for group in groups:
            print(f"Group: {group.name} ({group.full_path})")

        # Find a specific group
        my_group = groups.find("path=my-team")
        if my_group:
            # Access related resources
            for project in my_group.projects:
                print(f"Project: {project.name}")

            for member in my_group.members:
                print(f"Member: {member.username}")
    ```
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups"

    """
    Projects belonging to this group.

    Provides access to all projects within the group.
    """
    projects = HasMany(
        gitlab_rest_group_project_reference.GitlabRestGroupProjectReference,
        foreign_column_name="group_id",
    )

    """
    Access tokens for this group.

    Group access tokens can be used for API authentication with group-level permissions.
    """
    access_tokens = HasMany(
        gitlab_rest_group_access_token_reference.GitlabRestGroupAccessTokenReference,
        foreign_column_name="group_id",
    )

    """
    CI/CD variables defined for this group.

    These variables are available to all projects within the group.
    """
    variables = HasMany(
        gitlab_rest_group_variable_reference.GitlabRestGroupVariableReference,
        foreign_column_name="group_id",
    )

    """
    Subgroups within this group.

    Groups can be nested to create a hierarchy of teams and projects.
    """
    subgroups = HasMany(
        gitlab_rest_group_subgroup_reference.GitlabRestGroupSubgroupReference,
        foreign_column_name="group_id",
    )

    """
    Members of this group.

    Users who have been granted access to the group and its resources.
    """
    members = HasMany(
        gitlab_rest_group_member_reference.GitlabRestGroupMemberReference,
        foreign_column_name="group_id",
    )
