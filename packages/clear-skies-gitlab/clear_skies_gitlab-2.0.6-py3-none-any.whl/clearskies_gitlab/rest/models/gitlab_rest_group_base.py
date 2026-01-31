from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import (
    BelongsToModel,
    BelongsToSelf,
    Boolean,
    Datetime,
    Integer,
    Json,
    Select,
    String,
)

from clearskies_gitlab.rest.backends import GitlabRestBackend


class GitlabRestGroupBase(
    Model,
):
    """
    Base model for GitLab groups.

    This model provides the common fields and functionality shared by all group-related
    models (GitlabRestGroup, GitlabRestGroupSubgroup, etc.). It contains the core
    group attributes and search parameters.

    See https://docs.gitlab.com/api/groups/ for more details.

    Note: This is a base class and should typically not be used directly.
    Use GitlabRestGroup or GitlabRestGroupSubgroup instead.
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "groups"

    id_column_name = "id"

    backend = GitlabRestBackend()

    """
    The unique identifier for the group.
    """
    id = String()

    """
    URL to the group's GitLab page.
    """
    web_url = String()

    """
    The display name of the group.
    """
    name = String()

    """
    The URL-friendly path/slug of the group.
    """
    path = String()

    """
    A description of the group's purpose.
    """
    description = String()

    """
    The visibility level of the group.

    Values: "public", "internal", or "private".
    """
    visibility = String()

    """
    Whether sharing the group with other groups is locked.
    """
    share_with_group_lock = Boolean()

    """
    Whether two-factor authentication is required for group members.
    """
    require_two_factor_authentication = Boolean()

    """
    Grace period (in hours) for enabling two-factor authentication.
    """
    two_factor_grace_period = Integer()

    """
    Who can create projects in this group.

    Values: "noone", "maintainer", "developer".
    """
    project_creation_level = String()

    """
    Whether Auto DevOps is enabled for projects in this group.
    """
    auto_devops_enabled = Boolean()

    """
    Who can create subgroups in this group.

    Values: "owner", "maintainer".
    """
    subgroup_creation_level = String()

    """
    Whether email notifications are disabled for this group.
    """
    emails_disabled = Boolean()

    """
    Whether email notifications are enabled for this group.
    """
    emails_enabled = Boolean()

    """
    Whether mentions are disabled for this group.
    """
    mentions_disabled = String()

    """
    Whether Git LFS is enabled for projects in this group.
    """
    lfs_enabled = String()

    """
    Whether math rendering limits are enabled.
    """
    math_rendering_limits_enabled = Boolean()

    """
    Whether math rendering limits are locked.
    """
    lock_math_rendering_limits_enabled = Boolean()

    """
    The default branch for new projects in this group.
    """
    default_branch = String()

    """
    The default branch protection level.
    """
    default_branch_protection = String()

    """
    Default branch protection settings.
    """
    default_branch_protection_defaults = String()

    """
    URL to the group's avatar image.
    """
    avatar_url = String()

    """
    Whether users can request access to this group.
    """
    request_access_enabled = Boolean()

    """
    The full display name including parent groups.

    For example: "Parent Group / Child Group".
    """
    full_name = String()

    """
    The full path including parent groups.

    For example: "parent-group/child-group".
    """
    full_path = String()

    """
    The date and time when the group was created.
    """
    created_at = Datetime()

    """
    The ID of the parent group.

    Null for top-level groups.
    """
    parent_id = String()

    """
    The ID of the organization this group belongs to.
    """
    organization_id = String()

    """
    The shared runners setting for this group.

    Controls whether shared runners are available to projects.
    """
    shared_runners_setting = String()

    """
    Custom attributes attached to this group.
    """
    custom_attributes = Json()

    """
    Statistics about the group (storage, repository size, etc.).
    """
    statistics = Json()

    """
    LDAP Common Name for LDAP-synced groups.
    """
    ldap_cn = String()

    """
    LDAP access level for LDAP-synced groups.
    """
    ldap_access = String()

    """
    LDAP group links configuration.
    """
    ldap_group_links = Json()

    """
    SAML group links configuration.
    """
    saml_group_links = Json()

    """
    The ID of the project used for file templates.
    """
    file_template_project_id = String()

    """
    The date when the group was marked for deletion.
    """
    marked_for_deletion_on = Datetime()

    """
    The wiki access level for this group.
    """
    wiki_access_level = String()

    """
    The repository storage location for this group.
    """
    repository_storage = String()

    """
    Whether GitLab Duo features are enabled.
    """
    duo_features_enabled = Boolean()

    """
    Whether GitLab Duo features setting is locked.
    """
    lock_duo_features_enabled = Boolean()

    """
    Groups that this group is shared with.
    """
    shared_with_groups = Json()

    """
    The runners registration token for this group.

    Used to register new runners with this group.
    """
    runners_token = String()

    """
    The enabled Git access protocol.

    Values: "ssh", "http", "all".
    """
    enabled_git_access_protocol = String()

    """
    Whether sharing groups outside the hierarchy is prevented.
    """
    prevent_sharing_groups_outside_hierarchy = Boolean()

    """
    The shared runners compute minutes limit for this group.
    """
    shared_runners_minutes_limit = Integer()

    """
    Extra shared runners compute minutes for this group.
    """
    extra_shared_runners_minutes_limit = Integer()

    """
    Whether forking projects outside the group is prevented.
    """
    prevent_forking_outside_group = Boolean()

    """
    Whether service access token expiration is enforced.
    """
    service_access_tokens_expiration_enforced = Boolean()

    """
    Whether membership changes are locked.
    """
    membership_lock = Boolean()

    """
    IP address ranges allowed to access this group.
    """
    ip_restriction_ranges = Json()

    """
    Limit for unique project downloads.
    """
    unique_project_download_limit = String()

    """
    Interval in seconds for unique project download limit.
    """
    unique_project_download_limit_interval_in_seconds = Integer()

    """
    List of users to alert when download limit is exceeded.
    """
    unique_project_download_limit_alertlist = Json()

    """
    Whether to auto-ban users on excessive project downloads.
    """
    auto_ban_user_on_excessive_projects_download = Boolean()

    """
    Reference to the parent group.
    """
    parent_id = BelongsToSelf()

    """
    The parent group model.
    """
    parent = BelongsToModel("parent_id")

    ### Search params

    """
    List of group IDs to exclude from results.
    """
    skip_groups = Json()

    """
    Whether to include all available groups.
    """
    all_available = Boolean()

    """
    Search query to filter groups by name or path.
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
    Whether to only return groups owned by the current user.
    """
    owned = Boolean()

    """
    Minimum access level required to include a group.
    """
    min_access_level = Integer()

    """
    Whether to only return top-level groups.
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
