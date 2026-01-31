from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import (
    BelongsToModel,
    BelongsToSelf,
    Boolean,
    Datetime,
    HasMany,
    Integer,
    Json,
    Select,
    String,
)

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import (
    gitlab_rest_group_access_token,
    gitlab_rest_group_subgroup_reference,
    gitlab_rest_group_variable,
    gitlab_rest_project_reference,
)


class GitlabRestNamespace(Model):
    """
    Model for GitLab namespaces.

    This model provides access to the GitLab Namespaces API. Namespaces are
    containers for projects and can be either a user namespace or a group namespace.

    See https://docs.gitlab.com/api/namespaces/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestNamespace


    def my_function(namespaces: GitlabRestNamespace):
        # List all namespaces
        for ns in namespaces:
            print(f"Namespace: {ns.name} ({ns.kind})")
            print(f"Full path: {ns.full_path}")

        # Find a specific namespace
        my_ns = namespaces.find("path=my-team")
        if my_ns:
            print(f"Plan: {my_ns.plan}")
            print(f"Billable members: {my_ns.billable_members_count}")
    ```
    """

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "namespaces"

    id_column_name = "id"

    """
    The unique identifier for the namespace.
    """
    id = String()

    """
    The display name of the namespace.
    """
    name = String()

    """
    The URL-friendly path/slug of the namespace.
    """
    path = String()

    """
    The type of namespace.

    Values: "group" or "user".
    """
    kind = Select(allowed_values=["group", "user"])

    """
    The full path including parent namespaces.

    For example: "parent-group/child-group".
    """
    full_path = String()

    """
    URL to the namespace's avatar image.
    """
    avatar_url = String()

    """
    URL to the namespace's GitLab page.
    """
    web_url = String()

    """
    The number of billable members in this namespace.

    Only available for paid plans.
    """
    billable_members_count = Integer()

    """
    The subscription plan for this namespace.

    Values: "free", "premium", "ultimate", "bronze", "silver", "gold".
    """
    plan = Select(allowed_values=["free", "premium", "ultimate", "bronze", "silver", "gold"])

    """
    The end date of the current subscription.
    """
    end_date = Datetime()

    """
    The date when the trial period ends.
    """
    trial_ends_on = Datetime()

    """
    Whether this namespace is on a trial subscription.
    """
    trial = Boolean()

    """
    The total repository size in bytes.
    """
    root_repository_size = Integer()

    """
    The number of projects in this namespace.
    """
    projects_count = Integer()

    """
    The maximum number of seats used.
    """
    max_seats_used = Integer()

    """
    When the max seats used value last changed.
    """
    max_seats_used_changed_at = Datetime()

    """
    The number of seats currently in use.
    """
    seats_in_use = Integer()

    """
    The member count including descendants.
    """
    members_counts_with_descendants = Integer()

    """
    Projects in this namespace.
    """
    projects = HasMany(
        gitlab_rest_project_reference.GitlabRestProjectReference,
        foreign_column_name="group_id",
    )

    """
    Access tokens for this namespace.
    """
    access_tokens = HasMany(
        gitlab_rest_group_access_token.GitlabRestGroupAccessToken,
        foreign_column_name="group_id",
    )

    """
    CI/CD variables for this namespace.
    """
    variables = HasMany(
        gitlab_rest_group_variable.GitlabRestGroupVariable,
        foreign_column_name="group_id",
    )

    """
    Subgroups within this namespace.
    """
    subgroups = HasMany(
        gitlab_rest_group_subgroup_reference.GitlabRestGroupSubgroupReference,
        foreign_column_name="group_id",
    )

    """
    Reference to the parent namespace.
    """
    parent_id = BelongsToSelf()

    """
    The parent namespace model.
    """
    parent = BelongsToModel("parent_id")

    ### Search params

    """
    List of group IDs to exclude from results.
    """
    skip_groups = Json()

    """
    Whether to include all available namespaces.
    """
    all_available = Boolean()

    """
    Search query to filter namespaces.
    """
    search = String()

    """
    Field to order results by.
    """
    order_by = String()

    """
    Sort direction (asc or desc).
    """
    sort = String()

    """
    Filter by visibility level.
    """
    visibility = Select(allowed_values=["public", "internal", "private"])

    """
    Whether to include custom attributes in the response.
    """
    with_custom_attributes = Boolean()

    """
    Whether to only return namespaces owned by the current user.
    """
    owned = Boolean()

    """
    Minimum access level required to include a namespace.
    """
    min_access_level = Integer()

    """
    Whether to only return top-level namespaces.
    """
    top_level_only = Boolean()

    """
    Filter by repository storage location.
    """
    repository_storage = String()

    """
    Filter by deletion date.
    """
    marked_for_deletion_on = Datetime(date_format="%Y-%m-%d")
