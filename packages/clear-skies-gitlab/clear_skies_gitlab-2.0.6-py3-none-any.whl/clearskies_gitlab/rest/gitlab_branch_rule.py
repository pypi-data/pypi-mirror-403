from __future__ import annotations

from clearskies import Model
from clearskies.columns import Boolean, Datetime, Integer, Json, String


class GitlabBranchRule(Model):
    """
    Model representing a GitLab branch protection rule.

    Branch rules in GitLab define protection settings for branches, controlling
    who can push, merge, and unprotect branches. This model maps to the GitLab
    REST API response for protected branches.

    ```python
    from clearskies_gitlab.rest import GitlabBranchRule
    from clearskies_gitlab.rest.backends import GitlabRestBackend


    class ProjectBranchRule(GitlabBranchRule):
        backend = GitlabRestBackend()
        table_name = "projects/{project_id}/protected_branches"


    # Fetch all protected branches for a project
    rules = ProjectBranchRule.where(project_id="my-project").all()
    for rule in rules:
        print(f"Branch: {rule.name}, Protected: {rule.protected}")
    ```
    """

    """
    The unique identifier for the branch rule.
    """
    id = Integer()

    """
    The name or pattern of the protected branch (e.g., `main`, `release/*`).
    """
    name = String()

    """
    Whether the branch is protected.
    """
    protected = Boolean()

    """
    Whether developers are allowed to push to the branch.
    """
    developers_can_push = Boolean()

    """
    Whether developers are allowed to merge into the branch.
    """
    developers_can_merge = Boolean()

    """
    Whether the current user can push to the branch.
    """
    can_push = Boolean()

    """
    Whether this is the default branch of the repository.
    """
    default = Boolean()

    """
    The timestamp when the branch rule was created.
    """
    created_at = Datetime()

    """
    The timestamp when the branch rule was last updated.
    """
    updated_at = Datetime()

    """
    Whether code owner approval is required for merges to this branch.
    """
    code_owner_approval_required = Boolean()

    """
    JSON array of access levels that can unprotect the branch.

    Each entry contains information about who can remove protection from this branch.
    """
    unprotect_access_levels = Json()

    """
    JSON array of access levels that can push to the branch.

    Each entry contains information about who can push directly to this branch.
    """
    push_access_levels = Json()
