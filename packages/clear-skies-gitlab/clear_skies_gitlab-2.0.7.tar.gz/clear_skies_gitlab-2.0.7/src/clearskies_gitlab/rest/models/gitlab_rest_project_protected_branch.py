from __future__ import annotations

from typing import Self

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Boolean, Integer, Json, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectProtectedBranch(
    Model,
):
    """
    Model for GitLab project protected branches.

    This model represents a protected branch in a GitLab project. Protected branches are used to
    prevent unauthorized changes to important branches and enforce code review policies.

    See https://docs.gitlab.com/api/protected_branches/ for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectProtectedBranch


    def my_function(protected_branches: GitlabRestProjectProtectedBranch):
        # List all protected branches for a project
        for branch in protected_branches.where("project_id=123"):
            print(f"Branch: {branch.name}, Force push allowed: {branch.allow_force_push}")

        # Find a specific protected branch
        main_branch = protected_branches.find("name=main")
        if main_branch:
            print(
                f"Main branch requires code owner approval: {main_branch.code_owner_approval_required}"
            )
    ```
    """

    @classmethod
    def destination_name(cls: type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/protected_branches"

    id_column_name = "id"

    backend = GitlabRestBackend()

    """
    The ID of the protected branch.
    """
    id = Integer()

    """
    The name of the protected branch or wildcard pattern.

    Can be an exact branch name (e.g., "main") or a wildcard pattern (e.g., "release/*").
    """
    name = String()

    """
    Whether force push is allowed on this protected branch.

    If `True`, users with push access can force push to this branch.
    """
    allow_force_push = Boolean()

    """
    Whether code owner approval is required for pushes to this branch.

    If `True`, code owners must approve changes before they can be merged.
    This feature is available in GitLab Premium and Ultimate.
    """
    code_owner_approval_required = Boolean()

    """
    Whether the protection settings are inherited from the parent group.

    If `True`, the protection settings were inherited from the project's parent group.
    This field is only available in GitLab Premium and Ultimate.
    """
    inherited = Boolean()

    """
    Array of merge access level configurations.

    Each entry in the array contains:
    - `id`: ID of the merge access level configuration
    - `access_level`: Access level for merging (e.g., 40 for Maintainers)
    - `access_level_description`: Human-readable description of the access level
    - `user_id`: ID of the user with merge access (Premium and Ultimate only)
    - `group_id`: ID of the group with merge access (Premium and Ultimate only)

    Example:
    ```json
    [
        {
            "id": 2001,
            "access_level": 40,
            "access_level_description": "Maintainers"
        }
    ]
    ```
    """
    merge_access_levels = Json()

    """
    Array of push access level configurations.

    Each entry in the array contains:
    - `id`: ID of the push access level configuration
    - `access_level`: Access level for pushing (e.g., 40 for Maintainers)
    - `access_level_description`: Human-readable description of the access level
    - `user_id`: ID of the user with push access (Premium and Ultimate only)
    - `group_id`: ID of the group with push access (Premium and Ultimate only)
    - `deploy_key_id`: ID of the deploy key with push access

    Example:
    ```json
    [
        {
            "id": 1001,
            "access_level": 40,
            "access_level_description": "Maintainers"
        },
        {
            "id": 1002,
            "access_level": 40,
            "access_level_description": "Deploy key",
            "deploy_key_id": 1
        }
    ]
    ```
    """
    push_access_levels = Json()

    """
    Array of unprotect access level configurations.

    Each entry in the array contains:
    - `id`: ID of the unprotect access level configuration
    - `access_level`: Access level for unprotecting (e.g., 40 for Maintainers)
    - `access_level_description`: Human-readable description of the access level
    - `user_id`: ID of the user with unprotect access (Premium and Ultimate only)
    - `group_id`: ID of the group with unprotect access (Premium and Ultimate only)

    This defines who can unprotect the branch.
    """
    unprotect_access_levels = Json()

    """
    The ID of the project this protected branch belongs to.

    This is used to scope the API requests to a specific project.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this protected branch belongs to.

    Provides access to the full project object via the relationship.
    """
    project = BelongsToModel("project_id")
