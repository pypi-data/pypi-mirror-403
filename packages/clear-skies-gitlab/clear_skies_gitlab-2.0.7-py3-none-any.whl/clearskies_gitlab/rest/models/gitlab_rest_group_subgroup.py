from __future__ import annotations

from typing import Self

from clearskies.columns import HasMany, HasManySelf, String

from clearskies_gitlab.rest.models import (
    gitlab_rest_group_access_token_reference,
    gitlab_rest_group_base,
    gitlab_rest_group_member_reference,
    gitlab_rest_group_project_reference,
    gitlab_rest_group_variable_reference,
)


class GitlabRestGroupSubgroup(
    gitlab_rest_group_base.GitlabRestGroupBase,
):
    """
    Model for GitLab subgroups.

    This model provides access to subgroups within a parent group. Subgroups
    allow for hierarchical organization of projects and teams within GitLab.

    See https://docs.gitlab.com/api/groups/#list-a-groups-subgroups for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestGroupSubgroup


    def my_function(subgroups: GitlabRestGroupSubgroup):
        # List all subgroups of a parent group
        for subgroup in subgroups.where("group_id=123"):
            print(f"Subgroup: {subgroup.name}")
            print(f"Full path: {subgroup.full_path}")

            # Access nested subgroups
            for nested in subgroup.subgroups:
                print(f"  Nested: {nested.name}")

        # Find a specific subgroup
        team = subgroups.find("path=my-team")
        if team:
            for project in team.projects:
                print(f"Project: {project.name}")
    ```
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups/:group_id/subgroups"

    """
    The ID of the parent group.

    Used to scope API requests to subgroups of a specific parent group.
    """
    group_id = String()

    """
    Projects belonging to this subgroup.
    """
    projects = HasMany(
        gitlab_rest_group_project_reference.GitlabRestGroupProjectReference,
        foreign_column_name="group_id",
    )

    """
    Access tokens for this subgroup.
    """
    access_tokens = HasMany(
        gitlab_rest_group_access_token_reference.GitlabRestGroupAccessTokenReference,
        foreign_column_name="group_id",
    )

    """
    CI/CD variables defined for this subgroup.
    """
    variables = HasMany(
        gitlab_rest_group_variable_reference.GitlabRestGroupVariableReference,
        foreign_column_name="group_id",
    )

    """
    Nested subgroups within this subgroup.
    """
    subgroups = HasManySelf(
        foreign_column_name="group_id",
    )

    """
    Members of this subgroup.
    """
    members = HasMany(
        gitlab_rest_group_member_reference.GitlabRestGroupMemberReference,
        foreign_column_name="group_id",
    )
