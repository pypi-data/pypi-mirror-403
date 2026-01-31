from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from builtins import type as builtins_type

from clearskies import Model
from clearskies.columns import BelongsToId, BelongsToModel, Boolean, Integer, Json, Select, String

from clearskies_gitlab.rest.backends import GitlabRestBackend
from clearskies_gitlab.rest.models import gitlab_rest_project_reference


class GitlabRestProjectApprovalRule(
    Model,
):
    """
    Model for GitLab project approval rules.

    This model provides access to the GitLab Merge Request Approval Rules API
    for managing project-level approval rules. Approval rules define who must
    approve merge requests and how many approvals are required.

    See https://docs.gitlab.com/api/merge_request_approvals/#get-project-level-rules for more details.

    Example usage:

    ```python
    from clearskies_gitlab.rest.models import GitlabRestProjectApprovalRule


    def my_function(approval_rules: GitlabRestProjectApprovalRule):
        # List all approval rules for a project
        for rule in approval_rules.where("project_id=123"):
            print(f"Rule: {rule.name}")
            print(f"Approvals required: {rule.approvals_required}")
            print(f"Type: {rule.type}")

        # Find a specific rule
        code_owner_rule = approval_rules.find("project_id=123&type=code_owner")
        if code_owner_rule:
            print(f"Code owner approvers: {code_owner_rule.eligible_approvers}")
    ```
    """

    backend = GitlabRestBackend()

    @classmethod
    def destination_name(cls: builtins_type[Self]) -> str:
        """Return the slug of the api endpoint for this model."""
        return "projects/:project_id/approval_rules"

    id_column_name = "id"

    """
    The display name of the approval rule.
    """
    name = String()

    """
    The unique identifier for the approval rule.
    """
    id = Integer()

    """
    The type of approval rule.

    Values:
    - "regular": A standard approval rule
    - "code_owner": Automatically created from CODEOWNERS file
    - "report_approver": Created from security/compliance reports
    """
    type = Select(allowed_values=["regular", "code_owner", "report_approver"])

    """
    The number of approvals required for this rule.
    """
    approvals_required = Integer()

    """
    Whether this rule applies to all protected branches.

    When true, the rule is enforced on all protected branches.
    When false, it only applies to specific protected branches.
    """
    applies_to_all_protected_branches = Boolean()

    """
    The ID of the project this rule belongs to.
    """
    project_id = BelongsToId(gitlab_rest_project_reference.GitlabRestProjectReference)

    """
    The project model this rule belongs to.
    """
    project = BelongsToModel("project_id")

    """
    List of users who can approve merge requests under this rule.

    Contains user objects with id, name, username, etc.
    """
    eligible_approvers = Json()

    """
    List of users assigned to this approval rule.

    Contains user objects with id, name, username, etc.
    """
    users = Json()

    """
    List of groups assigned to this approval rule.

    Contains group objects with id, name, path, etc.
    """
    groups = Json()

    """
    List of protected branches this rule applies to.

    Only populated when applies_to_all_protected_branches is false.
    Contains branch objects with id, name, etc.
    """
    protected_branches = Json()

    """
    Whether this rule contains hidden groups.

    Hidden groups are groups the current user doesn't have access to view.
    """
    contains_hidden_groups = Boolean()
